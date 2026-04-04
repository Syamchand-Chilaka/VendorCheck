from fastapi import HTTPException
from supabase import Client

from app.schemas.me import MeResponse, UserInfo, WorkspaceInfo


def get_or_create_workspace_context(user_id: str, supabase: Client) -> MeResponse:
    """Load user from Supabase Auth, find or create workspace + membership."""

    # 1. Get user from Supabase Auth admin API
    try:
        auth_response = supabase.auth.admin.get_user_by_id(user_id)
    except Exception:
        raise HTTPException(
            status_code=401, detail="User not found in auth system")

    user = auth_response.user
    if not user:
        raise HTTPException(
            status_code=401, detail="User not found in auth system")

    email = user.email or ""
    email_verified = user.email_confirmed_at is not None
    display_name = (user.user_metadata or {}).get("display_name", "")
    if not display_name:
        display_name = email.split("@")[0] if email else "User"

    # 2. Reject unverified emails
    if not email_verified:
        raise HTTPException(
            status_code=403,
            detail="Email not verified. Please verify your email before continuing.",
        )

    # 3. Look for existing workspace membership (with workspace join)
    membership = (
        supabase.table("workspace_members")
        .select("workspace_id, role, workspaces(id, name)")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if membership.data:
        member = membership.data[0]
        workspace = member["workspaces"]
        return MeResponse(
            user=UserInfo(
                id=user_id,
                email=email,
                display_name=display_name,
                email_verified=True,
            ),
            workspace=WorkspaceInfo(
                id=workspace["id"],
                name=workspace["name"],
                role=member["role"],
            ),
        )

    # 4. Auto-create: profile + workspace + admin membership
    supabase.table("profiles").upsert(
        {"id": user_id, "display_name": display_name},
        on_conflict="id",
    ).execute()

    workspace_name = f"{display_name}'s Workspace"
    ws_result = (
        supabase.table("workspaces")
        .insert({"name": workspace_name, "created_by": user_id})
        .execute()
    )
    workspace_id = ws_result.data[0]["id"]

    supabase.table("workspace_members").insert(
        {"workspace_id": workspace_id, "user_id": user_id, "role": "admin"}
    ).execute()

    return MeResponse(
        user=UserInfo(
            id=user_id,
            email=email,
            display_name=display_name,
            email_verified=True,
        ),
        workspace=WorkspaceInfo(
            id=workspace_id,
            name=workspace_name,
            role="admin",
        ),
    )
