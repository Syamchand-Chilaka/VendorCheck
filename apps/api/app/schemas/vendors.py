from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class VendorCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    contact_email: str | None = None
    contact_phone: str | None = None
    metadata: dict = Field(default_factory=dict)


class VendorResponse(BaseModel):
    id: str
    name: str
    contact_email: str | None = None
    contact_phone: str | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class VendorListResponse(BaseModel):
    items: list[VendorResponse]