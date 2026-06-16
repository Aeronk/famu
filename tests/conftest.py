"""Pytest fixtures: an isolated in-memory SQLite DB + ASGI test client per test."""

from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.database.models  # noqa: F401 — registers all tables on Base.metadata
from app.database.base import Base
from app.database.session import get_session as real_get_session
from app.main import app


@pytest_asyncio.fixture
async def db():
    """Fresh in-memory SQLite + session factory for the test."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db) -> AsyncClient:
    async def override_get_session():
        async with db() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[real_get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---- helpers ---------------------------------------------------------------
async def register_tenant(client: AsyncClient, slug: str, email: str) -> dict:
    payload = {
        "tenant": {"name": slug.title(), "slug": slug, "type": "smallholder"},
        "admin_email": email,
        "admin_password": "Password123",
        "admin_full_name": "Admin User",
    }
    resp = await client.post("/api/v1/auth/register-tenant", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
