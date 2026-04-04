"""Tests for the stub analysis service — no DB or network needed."""

from app.services.analysis import analyze_paste_text


class TestAnalyzePasteText:
    def test_safe_input(self):
        """Clean text with no risk indicators → safe."""
        result = analyze_paste_text(
            "Acme Corp\n"
            "Please find our invoice attached.\n"
            "Best regards, John"
        )
        assert result.verdict == "safe"
        assert result.risk_score < 30
        assert result.vendor_name == "Acme Corp"

    def test_urgency_language_detected(self):
        """Text with urgency words → verify or higher."""
        result = analyze_paste_text(
            "ABC Plumbing LLC\n"
            "This is URGENT. Please update our bank details ASAP.\n"
            "New account: 123456789\n"
            "Routing: 021000021"
        )
        signal_types = [s.signal_type for s in result.signals]
        assert "urgency_language" in signal_types
        assert result.risk_score > 0

    def test_bank_change_detected(self):
        """Text with bank-change phrases → high-severity signal."""
        result = analyze_paste_text(
            "Vendor Services Inc\n"
            "We have updated bank details for our company.\n"
            "New account number: 9876543210\n"
            "Routing: 021000021\n"
            "Contact: billing@gmail.com"
        )
        signal_types = [s.signal_type for s in result.signals]
        assert "bank_change_detected" in signal_types
        # bank change + free email = high enough to block or verify
        assert result.verdict in ("verify", "blocked")

    def test_domain_mismatch_free_email(self):
        """Free email provider → domain_mismatch signal."""
        result = analyze_paste_text(
            "Widget Corp\n"
            "Please send payment to billing@yahoo.com\n"
        )
        signal_types = [s.signal_type for s in result.signals]
        assert "domain_mismatch" in signal_types

    def test_missing_fields(self):
        """No bank details in text → missing_fields signal."""
        result = analyze_paste_text("Hello, this is a generic message.")
        signal_types = [s.signal_type for s in result.signals]
        assert "missing_fields" in signal_types

    def test_extraction_bank_account(self):
        """Account and routing numbers are extracted and hashed/masked."""
        result = analyze_paste_text(
            "Test Vendor\n"
            "Account: 1234567890\n"
            "Routing: 021000021"
        )
        assert result.bank_account_masked == "****7890"
        assert result.bank_routing_masked == "****0021"
        assert result.bank_account_hash is not None
        assert result.bank_routing_hash is not None
        # Hashes should not be the raw value
        assert result.bank_account_hash != "1234567890"

    def test_extraction_email(self):
        result = analyze_paste_text(
            "Acme Co\nContact us at info@acme.com for details."
        )
        assert result.vendor_contact_email == "info@acme.com"

    def test_extraction_phone(self):
        result = analyze_paste_text(
            "Acme Co\nCall us at 555-012-3456."
        )
        assert result.vendor_contact_phone == "555-012-3456"

    def test_combined_high_risk(self):
        """Multiple risk indicators should push toward blocked."""
        result = analyze_paste_text(
            "ABC Plumbing LLC\n"
            "URGENT: We've changed our bank details immediately.\n"
            "Please update ASAP before the deadline.\n"
            "New account: 999888777\n"
            "Routing: 021000021\n"
            "Contact: billing@hotmail.com"
        )
        # Should have urgency + bank_change + domain_mismatch = high total
        assert result.verdict in ("verify", "blocked")
        assert result.risk_score >= 50

    def test_verdict_score_consistency(self):
        """Risk score and verdict are consistent."""
        result = analyze_paste_text("Acme Co\nJust a regular message.")
        if result.risk_score >= 60:
            assert result.verdict == "blocked"
        elif result.risk_score >= 30:
            assert result.verdict == "verify"
        else:
            assert result.verdict == "safe"
