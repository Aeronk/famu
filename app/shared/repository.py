"""Generic async repository (data-access layer).

``BaseRepository`` handles non-tenant entities (e.g. ``tenants``). Tenant-scoped
entities use ``app.tenancy.repository.TenantRepository`` which layers automatic
``tenant_id`` filtering on top of this.
"""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    model: type[ModelType]

    def __init__(self, session: AsyncSession):
        self.session = session

    # ---- read ----
    async def get(self, id: uuid.UUID | str) -> ModelType | None:
        return await self.session.get(self.model, id)

    async def find_one(self, **filters: Any) -> ModelType | None:
        stmt = select(self.model).filter_by(**filters).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        order_by: Any | None = None,
        **filters: Any,
    ) -> list[ModelType]:
        stmt = select(self.model).filter_by(**filters)
        stmt = stmt.order_by(order_by if order_by is not None else self.model.created_at.desc())
        stmt = stmt.offset(offset).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model).filter_by(**filters)
        return int((await self.session.execute(stmt)).scalar_one())

    # ---- write ----
    async def create(self, **data: Any) -> ModelType:
        obj = self.model(**data)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def add(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(self, obj: ModelType, **data: Any) -> ModelType:
        for key, value in data.items():
            setattr(obj, key, value)
        await self.session.flush()
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self.session.delete(obj)
        await self.session.flush()
