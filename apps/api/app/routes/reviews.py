from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import AuthContext, get_current_member
from app.schemas.reviews import ReviewTaskListResponse, ReviewTaskResponse, ResolveReviewTaskRequest
from app.services.reviews import list_review_tasks, resolve_review_task

router = APIRouter()


@router.get("/review-tasks", response_model=ReviewTaskListResponse)
async def get_review_tasks(
    auth: AuthContext = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
) -> ReviewTaskListResponse:
    return await list_review_tasks(auth, db)


@router.post("/review-tasks/{review_task_id}/resolve", response_model=ReviewTaskResponse)
async def post_review_task_resolve(
    review_task_id: str,
    payload: ResolveReviewTaskRequest,
    auth: AuthContext = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
) -> ReviewTaskResponse:
    return await resolve_review_task(review_task_id, payload, auth, db)