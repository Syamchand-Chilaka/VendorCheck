from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_token
from app.db.session import get_db
from app.deps import get_current_user
from app.models.orm import User
from app.schemas.me import MeResponse
from app.services.workspace import get_or_create_workspace_context

router = APIRouter()


@router.get("/me", response_model=MeResponse)
async def get_me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    """Return authenticated user's profile and tenant context.

    Auto-creates tenant and owner membership on first call.
    """
    return await get_or_create_workspace_context(user, db)
