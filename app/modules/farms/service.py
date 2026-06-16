from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import DomainEvent, event_bus
from app.modules.farms.models import Farm
from app.modules.farms.repository import FarmRepo
from app.modules.farms.schemas import FarmCreate, FarmUpdate


class FarmService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.tenant_id = tenant_id
        self.repo = FarmRepo(session, tenant_id)

    async def create(self, data: FarmCreate) -> Farm:
        farm = await self.repo.create(**data.model_dump())
        await event_bus.publish(
            DomainEvent(name="farm.created", tenant_id=str(self.tenant_id), payload={"farm_id": str(farm.id)})
        )
        return farm

    async def get(self, farm_id: uuid.UUID) -> Farm:
        return await self.repo.get_or_404(farm_id)

    async def list(self, *, offset: int, limit: int) -> tuple[list[Farm], int]:
        items = await self.repo.list(offset=offset, limit=limit)
        total = await self.repo.count()
        return items, total

    async def update(self, farm_id: uuid.UUID, data: FarmUpdate) -> Farm:
        farm = await self.repo.get_or_404(farm_id)
        return await self.repo.update(farm, **data.model_dump(exclude_unset=True))

    async def delete(self, farm_id: uuid.UUID) -> None:
        farm = await self.repo.get_or_404(farm_id)
        await self.repo.delete(farm)
