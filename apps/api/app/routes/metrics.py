from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import AuthContext, get_current_member
from app.schemas.metrics import MetricsSummaryResponse
from app.services.metrics import get_metrics_summary

router = APIRouter()


@router.get("/metrics/summary", response_model=MetricsSummaryResponse)
async def get_metrics(
    auth: AuthContext = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
) -> MetricsSummaryResponse:
    return await get_metrics_summary(auth, db)