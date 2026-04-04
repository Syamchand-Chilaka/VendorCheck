from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ResolveReviewTaskRequest(BaseModel):
    resolution: str = Field(min_length=1)


class ReviewTaskResponse(BaseModel):
    id: str
    document_id: str | None = None
    document_version_id: str | None = None
    check_request_id: str | None = None
    status: str
    priority: int
    resolution: str | None = None
    created_at: datetime
    updated_at: datetime


class ReviewTaskListResponse(BaseModel):
    items: list[ReviewTaskResponse]