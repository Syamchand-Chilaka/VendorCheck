from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import AuditLog, MetricEvent


async def log_audit_event(
    db: AsyncSession,
    *,
    tenant_id: str,
    user_id: str | None,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    details: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=json.dumps(details or {}),
        )
    )


async def record_metric_event(
    db: AsyncSession,
    *,
    tenant_id: str,
    event_type: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    value: int | None = None,
    metadata: dict | None = None,
) -> None:
    db.add(
        MetricEvent(
            tenant_id=tenant_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            value=value,
            metadata_=json.dumps(metadata or {}),
        )
    )