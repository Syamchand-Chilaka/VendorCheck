from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from supabase import Client

from app.auth import verify_token


@dataclass
class AuthContext:
    """Full auth context for routes that require workspace membership."""
    user_id: str
    workspace_id: str
    role: str


def get_supabase(request: Request) -> Client:
    """Get the Supabase client from app state."""
    return request.app.state.supabase


def get_current_member(
    user_id: str = Depends(verify_token),
    supabase: Client = Depends(get_supabase),
) -> AuthContext:
    """Verify JWT + load workspace membership. Returns 403 if no membership.

    Used by all endpoints except GET /me.
    """
    result = (
        supabase.table("workspace_members")
        .select("workspace_id, role")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=403,
            detail="No workspace membership found. Call GET /api/v1/me first.",
        )

    member = result.data[0]
    return AuthContext(
        user_id=user_id,
        workspace_id=member["workspace_id"],
        role=member["role"],
    )
