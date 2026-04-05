from __future__ import annotations

import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import AuthContext
from app.models.orm import Vendor
from app.schemas.vendors import VendorCreateRequest, VendorListResponse, VendorResponse
from app.services.audit import log_audit_event, record_metric_event


def _parse_metadata(value: str | None) -> dict:
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


def _to_response(vendor: Vendor) -> VendorResponse:
    return VendorResponse(
        id=vendor.id,
        name=vendor.name,
        contact_email=vendor.contact_email,
        contact_phone=vendor.contact_phone,
        metadata=_parse_metadata(vendor.metadata_),
        created_at=vendor.created_at,
        updated_at=vendor.updated_at,
    )


async def create_vendor(
    payload: VendorCreateRequest,
    auth: AuthContext,
    db: AsyncSession,
) -> VendorResponse:
    vendor = Vendor(
        tenant_id=auth.tenant_id,
        name=payload.name.strip(),
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        metadata_=json.dumps(payload.metadata),
    )
    db.add(vendor)
    await log_audit_event(
        db,
        tenant_id=auth.tenant_id,
        user_id=auth.user_id,
        action="vendor.created",
        entity_type="vendor",
        entity_id=vendor.id,
        details={"name": vendor.name},
    )
    await record_metric_event(
        db,
        tenant_id=auth.tenant_id,
        event_type="vendor_created",
        entity_type="vendor",
        entity_id=vendor.id,
    )
    await db.commit()
    await db.refresh(vendor)
    return _to_response(vendor)


async def list_vendors(auth: AuthContext, db: AsyncSession) -> VendorListResponse:
    result = await db.execute(
        select(Vendor)
        .where(Vendor.tenant_id == auth.tenant_id)
        .order_by(Vendor.created_at.desc())
    )
    return VendorListResponse(items=[_to_response(row) for row in result.scalars().all()])


async def get_vendor(vendor_id: str, auth: AuthContext, db: AsyncSession) -> VendorResponse:
    result = await db.execute(
        select(Vendor)
        .where(Vendor.id == vendor_id)
        .where(Vendor.tenant_id == auth.tenant_id)
    )
    vendor = result.scalar_one_or_none()
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return _to_response(vendor)
