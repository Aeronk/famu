from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tenants.models import Tenant
from app.modules.tenants.repository import TenantRepo
from app.modules.tenants.schemas import TenantCreate, TenantUpdate
from app.shared.exceptions import ConflictError, NotFoundError


class TenantService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TenantRepo(session)

    async def create(self, data: TenantCreate) -> Tenant:
        if await self.repo.find_one(slug=data.slug):
            raise ConflictError(f"Tenant slug '{data.slug}' is already taken")
        return await self.repo.create(**data.model_dump())

    async def get(self, tenant_id: uuid.UUID) -> Tenant:
        tenant = await self.repo.get(tenant_id)
        if not tenant:
            raise NotFoundError("Tenant not found")
        return tenant

    async def list(self, *, offset: int, limit: int) -> tuple[list[Tenant], int]:
        items = await self.repo.list(offset=offset, limit=limit)
        total = await self.repo.count()
        return items, total

    async def update(self, tenant_id: uuid.UUID, data: TenantUpdate) -> Tenant:
        tenant = await self.get(tenant_id)
        return await self.repo.update(tenant, **data.model_dump(exclude_unset=True))
