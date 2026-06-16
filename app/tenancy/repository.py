"""Tenant-scoped repository — the enforcement point for row-level isolation.

Every read/write is automatically constrained to ``tenant_id`` and every insert
is stamped with it. Super Admin flows may pass ``bypass_tenant=True`` for
explicit, audited cross-tenant access.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.exceptions import NotFoundError, TenantResolutionError
from app.shared.repository import BaseRepository, ModelType


class TenantRepository(BaseRepository[ModelType]):
    def __init__(
        self,
        session: AsyncSession,
        tenant_id: str | uuid.UUID | None,
        *,
        bypass_tenant: bool = False,
    ):
        super().__init__(session)
        self.bypass_tenant = bypass_tenant
        self.tenant_id = str(tenant_id) if tenant_id else None
        if not self.bypass_tenant and not self.tenant_id:
            raise TenantResolutionError("No tenant in context for a tenant-scoped operation")

    # ---- helpers ----
    def _scope(self, stmt):
        if self.bypass_tenant:
            return stmt
        return stmt.where(self.model.tenant_id == self.tenant_id)

    # ---- read ----
    async def get(self, id: uuid.UUID | str) -> ModelType | None:
        stmt = self._scope(select(self.model).where(self.model.id == id))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_or_404(self, id: uuid.UUID | str) -> ModelType:
        obj = await self.get(id)
        if obj is None:
            raise NotFoundError(f"{self.model.__name__} not found")
        return obj

    async def find_one(self, **filters: Any) -> ModelType | None:
        stmt = self._scope(select(self.model).filter_by(**filters)).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        order_by: Any | None = None,
        **filters: Any,
    ) -> list[ModelType]:
        stmt = self._scope(select(self.model).filter_by(**filters))
        stmt = stmt.order_by(order_by if order_by is not None else self.model.created_at.desc())
        stmt = stmt.offset(offset).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def count(self, **filters: Any) -> int:
        stmt = self._scope(
            select(func.count()).select_from(self.model).filter_by(**filters)
        )
        return int((await self.session.execute(stmt)).scalar_one())

    # ---- write ----
    async def create(self, **data: Any) -> ModelType:
        if not self.bypass_tenant:
            data.setdefault("tenant_id", self.tenant_id)
        obj = self.model(**data)
        self.session.add(obj)
        await self.session.flush()
        return obj
