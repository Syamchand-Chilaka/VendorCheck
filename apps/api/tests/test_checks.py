"""Tests for POST /api/v1/checks route — uses FastAPI test client with mocked deps."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.deps import AuthContext, get_current_member, get_supabase
from app.main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_auth():
    """Override auth dependency to return a fake workspace member."""
    ctx = AuthContext(user_id="test-user-id", workspace_id="test-ws-id", role="admin")
    app.dependency_overrides[get_current_member] = lambda: ctx
    yield ctx
    app.dependency_overrides.pop(get_current_member, None)


@pytest.fixture
def mock_supabase():
    """Override Supabase client dependency with a mock."""
    mock = MagicMock()
    app.dependency_overrides[get_supabase] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_supabase, None)


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Auth tests
# ---------------------------------------------------------------------------

class TestCheckAuth:
    def test_401_when_no_token(self, client):
        """POST /checks without auth → 401."""
        resp = client.post(
            "/api/v1/checks",
            data={"input_type": "paste_text", "raw_text": "hello"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

class TestCheckValidation:
    def test_422_when_empty_raw_text(self, client, mock_auth, mock_supabase):
        resp = client.post(
            "/api/v1/checks",
            data={"input_type": "paste_text", "raw_text": "   "},
        )
        assert resp.status_code == 422
        assert "raw_text" in resp.json()["detail"].lower()

    def test_422_when_raw_text_missing(self, client, mock_auth, mock_supabase):
        resp = client.post(
            "/api/v1/checks",
            data={"input_type": "paste_text"},
        )
        assert resp.status_code == 422

    def test_422_invalid_input_type(self, client, mock_auth, mock_supabase):
        resp = client.post(
            "/api/v1/checks",
            data={"input_type": "csv", "raw_text": "hello"},
        )
        assert resp.status_code == 422
        assert "input_type" in resp.json()["detail"].lower()

    def test_501_pdf_not_implemented(self, client, mock_auth, mock_supabase):
        resp = client.post(
            "/api/v1/checks",
            data={"input_type": "pdf", "raw_text": "ignored"},
        )
        assert resp.status_code == 501
        assert "pdf" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

class TestCheckCreation:
    def _setup_supabase_mock(self, mock_supabase):
        """Configure mock to simulate successful DB inserts."""
        # Prior check query returns no prior
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []

        # Profile lookup
        profiles_chain = MagicMock()
        profiles_chain.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
            {"display_name": "Test User"}
        ]

        # Check insert
        check_insert_chain = MagicMock()
        check_insert_chain.insert.return_value.execute.return_value.data = [{
            "id": "check-uuid-1",
            "workspace_id": "test-ws-id",
            "submitted_by": "test-user-id",
            "input_type": "paste_text",
            "raw_input_text": "test text",
            "vendor_name": "Test Vendor",
            "vendor_contact_email": None,
            "vendor_contact_phone": None,
            "bank_name": None,
            "bank_account_hash": None,
            "bank_routing_hash": None,
            "bank_account_masked": None,
            "bank_routing_masked": None,
            "status": "analyzed",
            "verdict": "safe",
            "verdict_explanation": "No risk.",
            "recommended_action": "Process normally.",
            "risk_score": 10,
            "prior_check_id": None,
            "bank_details_changed": None,
            "analysis_error": None,
            "decision": None,
            "decided_by": None,
            "decided_at": None,
            "decision_note": None,
            "created_at": "2026-04-04T14:30:00Z",
            "updated_at": "2026-04-04T14:30:00Z",
        }]

        # Signal insert
        signal_insert_chain = MagicMock()
        signal_insert_chain.insert.return_value.execute.return_value.data = [{
            "id": "signal-uuid-1",
            "check_request_id": "check-uuid-1",
            "signal_type": "missing_fields",
            "severity": "low",
            "title": "Missing expected fields",
            "description": "Could not extract: bank account number, routing number.",
            "created_at": "2026-04-04T14:30:00Z",
        }]

        # Route table() calls by table name
        def table_router(name):
            if name == "profiles":
                return profiles_chain
            elif name == "check_requests":
                # First call is prior-check lookup, second is insert
                # We need to handle both select and insert on check_requests
                check_chain = MagicMock()
                check_chain.select.return_value.eq.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
                check_chain.insert.return_value.execute.return_value.data = check_insert_chain.insert.return_value.execute.return_value.data
                return check_chain
            elif name == "risk_signals":
                return signal_insert_chain
            return MagicMock()

        mock_supabase.table.side_effect = table_router

    def test_happy_path_returns_201(self, client, mock_auth, mock_supabase):
        self._setup_supabase_mock(mock_supabase)
        resp = client.post(
            "/api/v1/checks",
            data={"input_type": "paste_text", "raw_text": "Test Vendor\nSome details here."},
        )
        assert resp.status_code == 201

    def test_response_shape(self, client, mock_auth, mock_supabase):
        self._setup_supabase_mock(mock_supabase)
        resp = client.post(
            "/api/v1/checks",
            data={"input_type": "paste_text", "raw_text": "Test Vendor\nSome details here."},
        )
        body = resp.json()
        # Required top-level fields from the contract
        assert "id" in body
        assert "status" in body
        assert "input_type" in body
        assert body["input_type"] == "paste_text"
        assert "verdict" in body
        assert "signals" in body
        assert isinstance(body["signals"], list)
        assert "submitted_by" in body
        assert "id" in body["submitted_by"]
        assert "display_name" in body["submitted_by"]
        assert "created_at" in body
        assert "decision" in body
        assert body["decision"] is None

    def test_signals_present(self, client, mock_auth, mock_supabase):
        self._setup_supabase_mock(mock_supabase)
        resp = client.post(
            "/api/v1/checks",
            data={"input_type": "paste_text", "raw_text": "Test Vendor\nSome details here."},
        )
        body = resp.json()
        assert len(body["signals"]) >= 1
        signal = body["signals"][0]
        assert "id" in signal
        assert "signal_type" in signal
        assert "severity" in signal
        assert "title" in signal
        assert "description" in signal
