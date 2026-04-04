from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class InitiateUploadRequest(BaseModel):
    vendor_id: str
    document_type: str = "other"
    title: str | None = None
    original_filename: str = Field(min_length=1)
    mime_type: str = Field(min_length=1)
    file_size_bytes: int = Field(ge=1)
    sha256: str | None = None
    document_id: str | None = None


class InitiateUploadResponse(BaseModel):
    document_id: str
    document_version_id: str
    version_no: int
    s3_bucket: str
    s3_key: str
    upload_url: str
    status: str


class CompleteUploadRequest(BaseModel):
    document_version_id: str


class CompleteUploadResponse(BaseModel):
    document_id: str
    document_version_id: str
    status: str
    workflow_run_id: str
    workflow_status: str


class DocumentResponse(BaseModel):
    id: str
    vendor_id: str
    vendor_name: str
    document_type: str | None = None
    title: str | None = None
    status: str
    current_version_no: int
    current_document_version_id: str | None = None
    current_filename: str | None = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]