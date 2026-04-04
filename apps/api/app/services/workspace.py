"""Workspace/tenant auto-creation service (Cognito + RDS)."""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import Membership, Tenant, User
from app.schemas.me import MeResponse, MembershipInfo, UserInfo


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "workspace"


async def get_or_create_workspace_context(user: User, db: AsyncSession) -> MeResponse:
    """Load user's tenant memberships. Auto-create tenant + owner membership if none exist."""

    # Find existing memberships
    result = await db.execute(
        select(Membership, Tenant)
        .join(Tenant, Membership.tenant_id == Tenant.id)
        .where(Membership.user_id == user.id)
    )
    rows = result.all()

    if rows:
        memberships = [
            MembershipInfo(
                tenant_id=t.id,
                tenant_name=t.name,
                role=m.role,
            )
            for m, t in rows
        ]
        return MeResponse(
            user=UserInfo(
                id=user.id,
                email=user.email,
                display_name=user.display_name,
                email_verified=user.email_verified,
            ),
            memberships=memberships,
        )

    # No memberships — auto-create tenant + owner membership
    display = user.display_name or user.email.split("@")[0]
    tenant_name = f"{display}'s Workspace"
    tenant = Tenant(
        name=tenant_name,
        slug=_slugify(tenant_name) + "-" + user.id[:8],
        created_by=user.id,
    )
    db.add(tenant)
    await db.flush()

    membership = Membership(
        tenant_id=tenant.id,
        user_id=user.id,
        role="owner",
    )
    db.add(membership)
    await db.commit()

    return MeResponse(
        user=UserInfo(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            email_verified=user.email_verified,
        ),
        memberships=[
            MembershipInfo(
                tenant_id=tenant.id,
                tenant_name=tenant.name,
                role="owner",
            )
        ],
    )
