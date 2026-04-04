"""Shared FastAPI dependencies for auth context and DB session."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_token
from app.db.session import get_db
from app.models.orm import Membership, User


@dataclass
class AuthContext:
    """Full auth context for routes that require tenant membership."""
    user_id: str
    tenant_id: str
    role: str
    cognito_sub: str


async def get_current_user(
    token_payload: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve Cognito token to a User row. Creates user on first request."""
    cognito_sub = token_payload["sub"]
    email = token_payload.get("email", "")

    result = await db.execute(
        select(User).where(User.cognito_sub == cognito_sub)
    )
    user = result.scalar_one_or_none()

    if user is None:
        # First login — create user row
        user = User(
            cognito_sub=cognito_sub,
            email=email,
            display_name=email.split("@")[0] if email else "User",
            email_verified=token_payload.get("email_verified", False),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


async def get_current_member(
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    """Verify the user has a membership in the requested tenant."""
    result = await db.execute(
        select(Membership)
        .where(Membership.tenant_id == x_tenant_id)
        .where(Membership.user_id == user.id)
    )
    membership = result.scalar_one_or_none()

    if membership is None:
        raise HTTPException(
            status_code=403,
            detail="No membership found for this tenant. Call GET /api/v1/me first.",
        )

    return AuthContext(
        user_id=user.id,
        tenant_id=membership.tenant_id,
        role=membership.role,
        cognito_sub=user.cognito_sub,
    )
