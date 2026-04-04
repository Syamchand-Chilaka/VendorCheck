"""Tenant-scoped database utilities.

Before each tenant-scoped query, call set_tenant() to establish
RLS context via SET LOCAL app.tenant_id.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_tenant(session: AsyncSession, tenant_id: str) -> None:
    """Set the RLS tenant context for this transaction."""
    await session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": tenant_id})
