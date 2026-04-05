from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import AuthContext
from app.models.orm import Document, DocumentVersion, ReviewTask
from app.schemas.reviews import ReviewTaskListResponse, ReviewTaskResponse, ResolveReviewTaskRequest
from app.services.audit import log_audit_event, record_metric_event


REVIEW_ROLES = {"owner", "admin", "reviewer"}


def _to_response(task: ReviewTask) -> ReviewTaskResponse:
    return ReviewTaskResponse(
        id=task.id,
        document_id=task.document_id,
        document_version_id=task.document_version_id,
        check_request_id=task.check_request_id,
        status=task.status,
        priority=task.priority,
        resolution=task.resolution,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _require_review_role(auth: AuthContext) -> None:
    if auth.role not in REVIEW_ROLES:
        raise HTTPException(
            status_code=403, detail="Insufficient role for review action")


async def list_review_tasks(auth: AuthContext, db: AsyncSession) -> ReviewTaskListResponse:
    _require_review_role(auth)
    result = await db.execute(
        select(ReviewTask)
        .where(ReviewTask.tenant_id == auth.tenant_id)
        .order_by(ReviewTask.priority.desc(), ReviewTask.created_at.desc())
    )
    return ReviewTaskListResponse(items=[_to_response(task) for task in result.scalars().all()])


async def resolve_review_task(
    review_task_id: str,
    payload: ResolveReviewTaskRequest,
    auth: AuthContext,
    db: AsyncSession,
) -> ReviewTaskResponse:
    _require_review_role(auth)
    result = await db.execute(
        select(ReviewTask)
        .where(ReviewTask.id == review_task_id)
        .where(ReviewTask.tenant_id == auth.tenant_id)
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Review task not found")

    task.status = "resolved"
    task.resolution = payload.resolution.strip()
    task.resolved_by = auth.user_id
    task.resolved_at = datetime.now(timezone.utc)

    # Propagate resolution to the linked document/version
    new_doc_status = "validated" if payload.resolution.strip() == "approved" else "rejected"
    if task.document_id:
        doc_result = await db.execute(
            select(Document)
            .where(Document.id == task.document_id)
            .where(Document.tenant_id == auth.tenant_id)
        )
        doc = doc_result.scalar_one_or_none()
        if doc:
            doc.status = new_doc_status
    if task.document_version_id:
        ver_result = await db.execute(
            select(DocumentVersion)
            .where(DocumentVersion.id == task.document_version_id)
            .where(DocumentVersion.tenant_id == auth.tenant_id)
        )
        ver = ver_result.scalar_one_or_none()
        if ver:
            ver.status = new_doc_status

    await log_audit_event(
        db,
        tenant_id=auth.tenant_id,
        user_id=auth.user_id,
        action="review_task.resolved",
        entity_type="review_task",
        entity_id=task.id,
        details={"resolution": task.resolution},
    )
    await record_metric_event(
        db,
        tenant_id=auth.tenant_id,
        event_type="review_task_resolved",
        entity_type="review_task",
        entity_id=task.id,
    )
    await db.commit()
    await db.refresh(task)
    return _to_response(task)
