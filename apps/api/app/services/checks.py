"""Service layer for creating and persisting checks."""

from __future__ import annotations

from supabase import Client

from app.deps import AuthContext
from app.schemas.checks import CreateCheckResponse, SignalResponse, SubmittedBy
from app.services.analysis import AnalysisResult, analyze_paste_text


def _find_prior_check(
    supabase: Client,
    workspace_id: str,
    vendor_name: str | None,
) -> dict | None:
    """Find the most recent analyzed check for the same vendor in this workspace."""
    if not vendor_name:
        return None

    result = (
        supabase.table("check_requests")
        .select("id, bank_account_hash, bank_routing_hash")
        .eq("workspace_id", workspace_id)
        .eq("vendor_name", vendor_name)
        .eq("status", "analyzed")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def _check_bank_details_changed(
    analysis: AnalysisResult, prior: dict | None
) -> bool | None:
    """Compare bank hashes against prior check. Returns None if no prior check."""
    if prior is None:
        return None

    prior_acct = prior.get("bank_account_hash")
    prior_routing = prior.get("bank_routing_hash")

    if not prior_acct and not prior_routing:
        return None
    if not analysis.bank_account_hash and not analysis.bank_routing_hash:
        return None

    acct_changed = (
        prior_acct and analysis.bank_account_hash
        and prior_acct != analysis.bank_account_hash
    )
    routing_changed = (
        prior_routing and analysis.bank_routing_hash
        and prior_routing != analysis.bank_routing_hash
    )

    return bool(acct_changed or routing_changed)


def create_paste_text_check(
    raw_text: str,
    auth: AuthContext,
    supabase: Client,
) -> CreateCheckResponse:
    """Full flow: analyze text → find prior → persist check + signals → return response."""

    # 1. Run stub analysis
    analysis = analyze_paste_text(raw_text)

    # 2. Prior-check comparison
    prior = _find_prior_check(supabase, auth.workspace_id, analysis.vendor_name)
    prior_check_id = prior["id"] if prior else None
    bank_details_changed = _check_bank_details_changed(analysis, prior)

    # 3. Get display name for submitted_by
    profile_result = (
        supabase.table("profiles")
        .select("display_name")
        .eq("id", auth.user_id)
        .limit(1)
        .execute()
    )
    display_name = profile_result.data[0]["display_name"] if profile_result.data else "User"

    # 4. Insert check_requests row
    check_row = {
        "workspace_id": auth.workspace_id,
        "submitted_by": auth.user_id,
        "input_type": "paste_text",
        "raw_input_text": raw_text,
        "vendor_name": analysis.vendor_name,
        "vendor_contact_email": analysis.vendor_contact_email,
        "vendor_contact_phone": analysis.vendor_contact_phone,
        "bank_name": analysis.bank_name,
        "bank_account_hash": analysis.bank_account_hash,
        "bank_routing_hash": analysis.bank_routing_hash,
        "bank_account_masked": analysis.bank_account_masked,
        "bank_routing_masked": analysis.bank_routing_masked,
        "status": "analyzed",
        "verdict": analysis.verdict,
        "verdict_explanation": analysis.verdict_explanation,
        "recommended_action": analysis.recommended_action,
        "risk_score": analysis.risk_score,
        "prior_check_id": prior_check_id,
        "bank_details_changed": bank_details_changed,
    }

    insert_result = supabase.table("check_requests").insert(check_row).execute()
    check = insert_result.data[0]

    # 5. Insert risk_signals rows
    signal_responses: list[SignalResponse] = []
    for sig in analysis.signals:
        sig_row = {
            "check_request_id": check["id"],
            "signal_type": sig.signal_type,
            "severity": sig.severity,
            "title": sig.title,
            "description": sig.description,
        }
        sig_result = supabase.table("risk_signals").insert(sig_row).execute()
        inserted = sig_result.data[0]
        signal_responses.append(SignalResponse(
            id=inserted["id"],
            signal_type=inserted["signal_type"],
            severity=inserted["severity"],
            title=inserted["title"],
            description=inserted["description"],
        ))

    # 6. Build response
    return CreateCheckResponse(
        id=check["id"],
        status=check["status"],
        input_type=check["input_type"],
        vendor_name=check.get("vendor_name"),
        vendor_contact_email=check.get("vendor_contact_email"),
        bank_name=check.get("bank_name"),
        bank_account_masked=check.get("bank_account_masked"),
        bank_routing_masked=check.get("bank_routing_masked"),
        bank_details_changed=check.get("bank_details_changed"),
        verdict=check.get("verdict"),
        verdict_explanation=check.get("verdict_explanation"),
        recommended_action=check.get("recommended_action"),
        risk_score=check.get("risk_score"),
        signals=signal_responses,
        prior_check_id=check.get("prior_check_id"),
        decision=None,
        submitted_by=SubmittedBy(id=auth.user_id, display_name=display_name),
        created_at=check["created_at"],
    )
