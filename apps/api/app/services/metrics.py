from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import AuthContext
from app.models.orm import CheckRequest, Document, ReviewTask, Vendor
from app.schemas.metrics import MetricsSummaryResponse


async def _count(db: AsyncSession, statement) -> int:
    result = await db.execute(statement)
    value = result.scalar_one()
    return int(value or 0)


async def get_metrics_summary(auth: AuthContext, db: AsyncSession) -> MetricsSummaryResponse:
    total_vendors = await _count(
        db,
        select(func.count()).select_from(Vendor).where(
            Vendor.tenant_id == auth.tenant_id),
    )
    total_documents = await _count(
        db,
        select(func.count()).select_from(Document).where(
            Document.tenant_id == auth.tenant_id),
    )
    total_checks = await _count(
        db,
        select(func.count()).select_from(CheckRequest).where(
            CheckRequest.tenant_id == auth.tenant_id),
    )
    open_review_tasks = await _count(
        db,
        select(func.count()).select_from(ReviewTask)
        .where(ReviewTask.tenant_id == auth.tenant_id)
        .where(ReviewTask.status != "resolved"),
    )
    approved_checks = await _count(
        db,
        select(func.count()).select_from(CheckRequest)
        .where(CheckRequest.tenant_id == auth.tenant_id)
        .where(CheckRequest.decision == "approved"),
    )
    held_checks = await _count(
        db,
        select(func.count()).select_from(CheckRequest)
        .where(CheckRequest.tenant_id == auth.tenant_id)
        .where(CheckRequest.decision == "held"),
    )
    rejected_checks = await _count(
        db,
        select(func.count()).select_from(CheckRequest)
        .where(CheckRequest.tenant_id == auth.tenant_id)
        .where(CheckRequest.decision == "rejected"),
    )
    return MetricsSummaryResponse(
        total_vendors=total_vendors,
        total_documents=total_documents,
        total_checks=total_checks,
        open_review_tasks=open_review_tasks,
        approved_checks=approved_checks,
        held_checks=held_checks,
        rejected_checks=rejected_checks,
    )
