from fastapi import APIRouter, Depends
from supabase import Client

from app.auth import verify_token
from app.deps import get_supabase
from app.schemas.me import MeResponse
from app.services.workspace import get_or_create_workspace_context

router = APIRouter()


@router.get("/me", response_model=MeResponse)
def get_me(
    user_id: str = Depends(verify_token),
    supabase: Client = Depends(get_supabase),
) -> MeResponse:
    """Return authenticated user's profile and workspace context.

    Auto-creates profile, workspace, and admin membership on first call
    for verified users.
    """
    return get_or_create_workspace_context(user_id, supabase)
