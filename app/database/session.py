"""Async SQLAlchemy engine and session factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a transactional session.

    Commits on success, rolls back on exception. Tenant scoping is applied by
    the repositories; optional Postgres RLS is applied via ``set_tenant_guc``.
    """
    from app.tenancy.context import current_tenant_id

    async with SessionLocal() as session:
        try:
            await set_tenant_guc(session, current_tenant_id())  # no-op unless ENABLE_RLS
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def set_tenant_guc(session: AsyncSession, tenant_id: str | None) -> None:
    """Defense-in-depth: set the Postgres GUC used by RLS policies.

    Only meaningful when ``ENABLE_RLS=true`` and policies are created in the DB.
    """
    if not settings.ENABLE_RLS or tenant_id is None:
        return
    if engine.dialect.name != "postgresql":  # GUC/RLS are Postgres-only
        return
    await session.execute(
        text("SELECT set_config('app.current_tenant', :tid, true)"),
        {"tid": str(tenant_id)},
    )
