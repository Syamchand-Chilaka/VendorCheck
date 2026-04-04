"""Shared test fixtures for VendorCheck API tests."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth import verify_token
from app.config import Settings, get_settings
from app.db.session import Base, get_db
from app.deps import AuthContext, get_current_member, get_current_user
from app.main import app
from app.models.orm import Membership, Tenant, User


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
async def db_session(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture()
async def seed_data(db_session: AsyncSession):
    """Seed a tenant, user, and membership for tests."""
    tenant = Tenant(
        id="test-tenant-id",
        name="Test Workspace",
        slug="test-workspace",
        created_by="test-user-id",
    )
    user = User(
        id="test-user-id",
        cognito_sub="cognito-sub-123",
        email="admin@test.com",
        display_name="Test User",
        email_verified=True,
    )
    membership = Membership(
        id=str(uuid.uuid4()),
        tenant_id="test-tenant-id",
        user_id="test-user-id",
        role="owner",
    )
    db_session.add_all([tenant, user, membership])
    await db_session.commit()
    return {"tenant": tenant, "user": user, "membership": membership}


@pytest.fixture()
async def client(db_engine, seed_data):
    """Async test client with DB and auth overrides."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    def override_verify_token():
        return {"sub": "cognito-sub-123", "email": "admin@test.com", "email_verified": True}

    async def override_get_current_user():
        async with factory() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.cognito_sub == "cognito-sub-123")
            )
            return result.scalar_one()

    async def override_get_current_member():
        return AuthContext(
            user_id="test-user-id",
            tenant_id="test-tenant-id",
            role="owner",
            cognito_sub="cognito-sub-123",
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_token] = override_verify_token
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_member] = override_get_current_member

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture()
async def unauthed_client():
    """Async test client with NO auth overrides."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
