from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.deps import AuthContext
from app.models.orm import Document, DocumentVersion, Vendor
from app.schemas.documents import (
    CompleteUploadRequest,
    CompleteUploadResponse,
    DocumentListResponse,
    DocumentResponse,
    InitiateUploadRequest,
    InitiateUploadResponse,
)
from app.services.audit import log_audit_event, record_metric_event
from app.services.storage import build_document_s3_key, generate_upload_url
from app.services.workflow import start_document_workflow


def _to_document_response(document: Document, vendor: Vendor, version: DocumentVersion | None) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        document_type=document.document_type,
        title=document.title,
        status=document.status,
        current_version_no=document.current_version_no,
        current_document_version_id=version.id if version else None,
        current_filename=version.original_filename if version else None,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


async def _get_vendor_or_404(vendor_id: str, auth: AuthContext, db: AsyncSession) -> Vendor:
    result = await db.execute(
        select(Vendor)
        .where(Vendor.id == vendor_id)
        .where(Vendor.tenant_id == auth.tenant_id)
    )
    vendor = result.scalar_one_or_none()
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


async def initiate_document_upload(
    payload: InitiateUploadRequest,
    auth: AuthContext,
    db: AsyncSession,
) -> InitiateUploadResponse:
    vendor = await _get_vendor_or_404(payload.vendor_id, auth, db)
    settings = get_settings()

    if payload.document_id:
        existing_result = await db.execute(
            select(Document)
            .where(Document.id == payload.document_id)
            .where(Document.tenant_id == auth.tenant_id)
        )
        document = existing_result.scalar_one_or_none()
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        version_no = document.current_version_no + 1
        document.current_version_no = version_no
        document.status = "uploaded"
        if payload.title is not None:
            document.title = payload.title
        if payload.document_type:
            document.document_type = payload.document_type
    else:
        document = Document(
            tenant_id=auth.tenant_id,
            vendor_id=vendor.id,
            document_type=payload.document_type,
            title=payload.title,
            status="uploaded",
            current_version_no=1,
            created_by=auth.user_id,
        )
        db.add(document)
        await db.flush()
        version_no = 1

    s3_key = build_document_s3_key(
        auth.tenant_id,
        vendor.id,
        document.id,
        version_no,
        payload.original_filename,
    )
    version = DocumentVersion(
        document_id=document.id,
        tenant_id=auth.tenant_id,
        version_no=version_no,
        status="uploaded",
        s3_bucket=settings.s3_documents_bucket or "local-bucket",
        s3_key=s3_key,
        original_filename=payload.original_filename,
        mime_type=payload.mime_type,
        file_size_bytes=payload.file_size_bytes,
        sha256=payload.sha256,
        created_by=auth.user_id,
    )
    db.add(version)

    await log_audit_event(
        db,
        tenant_id=auth.tenant_id,
        user_id=auth.user_id,
        action="document.upload_initiated",
        entity_type="document",
        entity_id=document.id,
        details={"document_version_id": version.id,
                 "filename": payload.original_filename},
    )
    await record_metric_event(
        db,
        tenant_id=auth.tenant_id,
        event_type="document_upload_initiated",
        entity_type="document",
        entity_id=document.id,
        value=payload.file_size_bytes,
    )
    await db.commit()
    await db.refresh(document)
    await db.refresh(version)

    return InitiateUploadResponse(
        document_id=document.id,
        document_version_id=version.id,
        version_no=version.version_no,
        s3_bucket=version.s3_bucket or "",
        s3_key=version.s3_key or "",
        upload_url=generate_upload_url(
            version.s3_bucket or "", version.s3_key or "", payload.mime_type),
        status=document.status,
    )


async def complete_document_upload(
    document_id: str,
    payload: CompleteUploadRequest,
    auth: AuthContext,
    db: AsyncSession,
) -> CompleteUploadResponse:
    result = await db.execute(
        select(Document, Vendor, DocumentVersion)
        .join(Vendor, Vendor.id == Document.vendor_id)
        .join(
            DocumentVersion,
            and_(
                DocumentVersion.document_id == Document.id,
                DocumentVersion.id == payload.document_version_id,
            ),
        )
        .where(Document.id == document_id)
        .where(Document.tenant_id == auth.tenant_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(
            status_code=404, detail="Document or version not found")

    document, vendor, version = row
    document.status = "queued"
    version.status = "queued"
    workflow_run = await start_document_workflow(
        db,
        tenant_id=auth.tenant_id,
        document=document,
        version=version,
        vendor=vendor,
    )
    await db.commit()

    return CompleteUploadResponse(
        document_id=document.id,
        document_version_id=version.id,
        status=document.status,
        workflow_run_id=workflow_run.id,
        workflow_status=workflow_run.status,
    )


async def list_documents(auth: AuthContext, db: AsyncSession) -> DocumentListResponse:
    result = await db.execute(
        select(Document, Vendor)
        .join(Vendor, Vendor.id == Document.vendor_id)
        .where(Document.tenant_id == auth.tenant_id)
        .order_by(Document.created_at.desc())
    )
    items: list[DocumentResponse] = []
    for document, vendor in result.all():
        version_result = await db.execute(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document.id)
            .where(DocumentVersion.version_no == document.current_version_no)
        )
        version = version_result.scalar_one_or_none()
        items.append(_to_document_response(document, vendor, version))
    return DocumentListResponse(items=items)


async def get_document(document_id: str, auth: AuthContext, db: AsyncSession) -> DocumentResponse:
    result = await db.execute(
        select(Document, Vendor)
        .join(Vendor, Vendor.id == Document.vendor_id)
        .where(Document.id == document_id)
        .where(Document.tenant_id == auth.tenant_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Document not found")
    document, vendor = row
    version_result = await db.execute(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document.id)
        .where(DocumentVersion.version_no == document.current_version_no)
    )
    version = version_result.scalar_one_or_none()
    return _to_document_response(document, vendor, version)
