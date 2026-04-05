"""Service layer for creating and persisting checks (RDS + SQLAlchemy)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import AuthContext
from app.models.orm import CheckRequest, RiskSignal, User
from app.schemas.checks import (
    CheckDecisionRequest,
    CheckDecisionResponse,
    CheckDetailResponse,
    CheckListItemResponse,
    CheckListResponse,
    CreateCheckResponse,
    SignalResponse,
    SubmittedBy,
)
from app.services.audit import log_audit_event, record_metric_event
from app.services.analysis import AnalysisResult, analyze_paste_text


DECISION_ROLES = {"owner", "admin", "reviewer"}


async def _find_prior_check(
    db: AsyncSession,
    tenant_id: str,
    vendor_name: str | None,
) -> CheckRequest | None:
    if not vendor_name:
        return None
    result = await db.execute(
        select(CheckRequest)
        .where(CheckRequest.tenant_id == tenant_id)
        .where(CheckRequest.vendor_name == vendor_name)
        .where(CheckRequest.status == "analyzed")
        .order_by(CheckRequest.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def _check_bank_details_changed(
    analysis: AnalysisResult, prior: CheckRequest | None
) -> bool | None:
    if prior is None:
        return None
    prior_acct = prior.bank_account_hash
    prior_routing = prior.bank_routing_hash
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


async def create_paste_text_check(
    raw_text: str,
    auth: AuthContext,
    db: AsyncSession,
) -> CreateCheckResponse:
    """Full flow: analyze text → find prior → persist check + signals → return response."""

    # 1. Run stub analysis
    analysis = analyze_paste_text(raw_text)

    # 2. Prior-check comparison
    prior = await _find_prior_check(db, auth.tenant_id, analysis.vendor_name)
    prior_check_id = prior.id if prior else None
    bank_details_changed = _check_bank_details_changed(analysis, prior)

    # 3. Get display name
    result = await db.execute(select(User).where(User.id == auth.user_id))
    user = result.scalar_one_or_none()
    display_name = user.display_name if user else "User"

    # 4. Insert check_requests row
    check = CheckRequest(
        tenant_id=auth.tenant_id,
        submitted_by=auth.user_id,
        input_type="paste_text",
        raw_input_text=raw_text,
        vendor_name=analysis.vendor_name,
        vendor_contact_email=analysis.vendor_contact_email,
        vendor_contact_phone=analysis.vendor_contact_phone,
        bank_name=analysis.bank_name,
        bank_account_hash=analysis.bank_account_hash,
        bank_routing_hash=analysis.bank_routing_hash,
        bank_account_masked=analysis.bank_account_masked,
        bank_routing_masked=analysis.bank_routing_masked,
        status="analyzed",
        verdict=analysis.verdict,
        verdict_explanation=analysis.verdict_explanation,
        recommended_action=analysis.recommended_action,
        risk_score=analysis.risk_score,
        prior_check_id=prior_check_id,
        bank_details_changed=bank_details_changed,
    )
    db.add(check)
    await db.flush()

    # 5. Insert risk_signals
    signal_responses: list[SignalResponse] = []
    for sig in analysis.signals:
        rs = RiskSignal(
            tenant_id=auth.tenant_id,
            check_request_id=check.id,
            signal_type=sig.signal_type,
            severity=sig.severity,
            title=sig.title,
            description=sig.description,
        )
        db.add(rs)
        await db.flush()
        signal_responses.append(SignalResponse(
            id=rs.id,
            signal_type=rs.signal_type,
            severity=rs.severity,
            title=rs.title,
            description=rs.description,
        ))

    await db.commit()

    # 6. Build response
    return CreateCheckResponse(
        id=check.id,
        status=check.status,
        input_type=check.input_type,
        vendor_name=check.vendor_name,
        vendor_contact_email=check.vendor_contact_email,
        bank_name=check.bank_name,
        bank_account_masked=check.bank_account_masked,
        bank_routing_masked=check.bank_routing_masked,
        bank_details_changed=check.bank_details_changed,
        verdict=check.verdict,
        verdict_explanation=check.verdict_explanation,
        recommended_action=check.recommended_action,
        risk_score=check.risk_score,
        signals=signal_responses,
        prior_check_id=check.prior_check_id,
        decision=None,
        submitted_by=SubmittedBy(id=auth.user_id, display_name=display_name),
        created_at=check.created_at,
    )


async def list_checks(auth: AuthContext, db: AsyncSession) -> CheckListResponse:
    result = await db.execute(
        select(CheckRequest)
        .where(CheckRequest.tenant_id == auth.tenant_id)
        .order_by(CheckRequest.created_at.desc())
    )
    return CheckListResponse(
        items=[
            CheckListItemResponse(
                id=check.id,
                status=check.status,
                input_type=check.input_type,
                vendor_name=check.vendor_name,
                verdict=check.verdict,
                risk_score=check.risk_score,
                decision=check.decision,
                created_at=check.created_at,
            )
            for check in result.scalars().all()
        ]
    )


async def get_check_detail(check_id: str, auth: AuthContext, db: AsyncSession) -> CheckDetailResponse:
    check_result = await db.execute(
        select(CheckRequest).where(CheckRequest.id == check_id).where(
            CheckRequest.tenant_id == auth.tenant_id)
    )
    check = check_result.scalar_one_or_none()
    if check is None:
        raise HTTPException(status_code=404, detail="Check not found")

    user_result = await db.execute(select(User).where(User.id == check.submitted_by))
    user = user_result.scalar_one_or_none()
    signal_result = await db.execute(
        select(RiskSignal)
        .where(RiskSignal.check_request_id == check.id)
        .order_by(RiskSignal.created_at.asc())
    )
    signals = [
        SignalResponse(
            id=signal.id,
            signal_type=signal.signal_type,
            severity=signal.severity,
            title=signal.title,
            description=signal.description,
        )
        for signal in signal_result.scalars().all()
    ]
    return CheckDetailResponse(
        id=check.id,
        status=check.status,
        input_type=check.input_type,
        vendor_name=check.vendor_name,
        vendor_contact_email=check.vendor_contact_email,
        vendor_contact_phone=check.vendor_contact_phone,
        bank_name=check.bank_name,
        bank_account_masked=check.bank_account_masked,
        bank_routing_masked=check.bank_routing_masked,
        bank_details_changed=check.bank_details_changed,
        verdict=check.verdict,
        verdict_explanation=check.verdict_explanation,
        recommended_action=check.recommended_action,
        risk_score=check.risk_score,
        signals=signals,
        prior_check_id=check.prior_check_id,
        decision=check.decision,
        decision_note=check.decision_note,
        decided_at=check.decided_at,
        analysis_error=check.analysis_error,
        submitted_by=SubmittedBy(
            id=check.submitted_by,
            display_name=user.display_name if user else "User",
        ),
        created_at=check.created_at,
        raw_input_text=check.raw_input_text,
    )


async def decide_check(
    check_id: str,
    payload: CheckDecisionRequest,
    auth: AuthContext,
    db: AsyncSession,
) -> CheckDecisionResponse:
    if auth.role not in DECISION_ROLES:
        raise HTTPException(
            status_code=403, detail="Insufficient role for decision action")
    if payload.decision not in {"approved", "held", "rejected"}:
        raise HTTPException(status_code=422, detail="Invalid decision")

    result = await db.execute(
        select(CheckRequest)
        .where(CheckRequest.id == check_id)
        .where(CheckRequest.tenant_id == auth.tenant_id)
    )
    check = result.scalar_one_or_none()
    if check is None:
        raise HTTPException(status_code=404, detail="Check not found")
    if check.decision is not None:
        raise HTTPException(
            status_code=409, detail="Decision already recorded")

    check.decision = payload.decision
    check.decision_note = payload.note
    check.decided_by = auth.user_id
    check.decided_at = datetime.now(timezone.utc)

    await log_audit_event(
        db,
        tenant_id=auth.tenant_id,
        user_id=auth.user_id,
        action="check.decision_recorded",
        entity_type="check_request",
        entity_id=check.id,
        details={"decision": payload.decision},
    )
    await record_metric_event(
        db,
        tenant_id=auth.tenant_id,
        event_type="check_decision_recorded",
        entity_type="check_request",
        entity_id=check.id,
    )
    await db.commit()
    return CheckDecisionResponse(
        id=check.id,
        decision=check.decision,
        decision_note=check.decision_note,
        decided_at=check.decided_at,
    )
