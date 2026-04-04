from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SubmittedBy(BaseModel):
    id: str
    display_name: str


class SignalResponse(BaseModel):
    id: str
    signal_type: str
    severity: str
    title: str
    description: str


class CreateCheckResponse(BaseModel):
    """Response for POST /api/v1/checks — matches locked API contract."""

    id: str
    status: str
    input_type: str
    vendor_name: str | None = None
    vendor_contact_email: str | None = None
    bank_name: str | None = None
    bank_account_masked: str | None = None
    bank_routing_masked: str | None = None
    bank_details_changed: bool | None = None
    verdict: str | None = None
    verdict_explanation: str | None = None
    recommended_action: str | None = None
    risk_score: int | None = None
    signals: list[SignalResponse] = []
    prior_check_id: str | None = None
    decision: str | None = None
    analysis_error: str | None = None
    submitted_by: SubmittedBy
    created_at: datetime


class CheckListItemResponse(BaseModel):
    id: str
    status: str
    input_type: str
    vendor_name: str | None = None
    verdict: str | None = None
    risk_score: int | None = None
    decision: str | None = None
    created_at: datetime


class CheckListResponse(BaseModel):
    items: list[CheckListItemResponse]


class CheckDetailResponse(CreateCheckResponse):
    raw_input_text: str | None = None
    vendor_contact_phone: str | None = None
    bank_routing_masked: str | None = None
    decision_note: str | None = None
    decided_at: datetime | None = None


class CheckDecisionRequest(BaseModel):
    decision: str = Field(min_length=1)
    note: str | None = None


class CheckDecisionResponse(BaseModel):
    id: str
    decision: str
    decision_note: str | None = None
    decided_at: datetime
