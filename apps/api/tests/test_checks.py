"""Tests for POST /api/v1/checks route — uses async test client with SQLite DB."""

import pytest
from httpx import AsyncClient


class TestCheckAuth:
    @pytest.mark.asyncio
    async def test_401_when_no_token(self, unauthed_client: AsyncClient):
        """POST /checks without auth → 401."""
        resp = await unauthed_client.post(
            "/api/v1/checks",
            data={"input_type": "paste_text", "raw_text": "hello"},
        )
        assert resp.status_code == 401


class TestCheckValidation:
    @pytest.mark.asyncio
    async def test_422_when_empty_raw_text(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/checks",
            data={"input_type": "paste_text", "raw_text": "   "},
        )
        assert resp.status_code == 422
        assert "raw_text" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_422_when_raw_text_missing(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/checks",
            data={"input_type": "paste_text"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_422_invalid_input_type(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/checks",
            data={"input_type": "csv", "raw_text": "hello"},
        )
        assert resp.status_code == 422
        assert "input_type" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_501_pdf_not_implemented(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/checks",
            data={"input_type": "pdf", "raw_text": "ignored"},
        )
        assert resp.status_code == 501
        assert "pdf" in resp.json()["detail"].lower()


class TestCheckCreation:
    @pytest.mark.asyncio
    async def test_happy_path_returns_201(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/checks",
            data={"input_type": "paste_text",
                  "raw_text": "Test Vendor\nSome details here."},
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_response_shape(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/checks",
            data={"input_type": "paste_text",
                  "raw_text": "Test Vendor\nSome details here."},
        )
        body = resp.json()
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

    @pytest.mark.asyncio
    async def test_signals_present(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/checks",
            data={"input_type": "paste_text",
                  "raw_text": "Test Vendor\nSome details here."},
        )
        body = resp.json()
        assert len(body["signals"]) >= 1
        signal = body["signals"][0]
        assert "id" in signal
        assert "signal_type" in signal
        assert "severity" in signal
        assert "title" in signal
        assert "description" in signal

    @pytest.mark.asyncio
    async def test_list_and_detail(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/v1/checks",
            data={"input_type": "paste_text",
                  "raw_text": "Test Vendor\nSome details here."},
            headers={"X-Tenant-Id": "test-tenant-id"},
        )
        check_id = create_resp.json()["id"]

        list_resp = await client.get(
            "/api/v1/checks",
            headers={"X-Tenant-Id": "test-tenant-id"},
        )
        assert list_resp.status_code == 200
        assert len(list_resp.json()["items"]) == 1

        detail_resp = await client.get(
            f"/api/v1/checks/{check_id}",
            headers={"X-Tenant-Id": "test-tenant-id"},
        )
        assert detail_resp.status_code == 200
        assert detail_resp.json()["id"] == check_id

    @pytest.mark.asyncio
    async def test_decision_recorded_once(self, client: AsyncClient):
        create_resp = await client.post(
            "/api/v1/checks",
            data={"input_type": "paste_text",
                  "raw_text": "Test Vendor\nSome details here."},
            headers={"X-Tenant-Id": "test-tenant-id"},
        )
        check_id = create_resp.json()["id"]

        decision_resp = await client.post(
            f"/api/v1/checks/{check_id}/decision",
            json={"decision": "approved", "note": "Looks valid"},
            headers={"X-Tenant-Id": "test-tenant-id"},
        )
        assert decision_resp.status_code == 200
        assert decision_resp.json()["decision"] == "approved"

        second_resp = await client.post(
            f"/api/v1/checks/{check_id}/decision",
            json={"decision": "held"},
            headers={"X-Tenant-Id": "test-tenant-id"},
        )
        assert second_resp.status_code == 409
