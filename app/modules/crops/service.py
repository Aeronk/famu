from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import DomainEvent, event_bus
from app.modules.crops.models import Activity, CropCycle, CropInput, Harvest
from app.modules.crops.repository import (
    ActivityRepo,
    CropCycleRepo,
    CropInputRepo,
    HarvestRepo,
)
from app.modules.crops.schemas import (
    ActivityCreate,
    CropCycleCreate,
    CropCycleUpdate,
    CropInputCreate,
    CropTimeline,
    HarvestCreate,
    TimelineEvent,
)


class CropService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.cycles = CropCycleRepo(session, tenant_id)
        self.inputs = CropInputRepo(session, tenant_id)
        self.harvests = HarvestRepo(session, tenant_id)
        self.activities = ActivityRepo(session, tenant_id)

    # ---- cycles ----
    async def create_cycle(self, data: CropCycleCreate) -> CropCycle:
        cycle = await self.cycles.create(**data.model_dump())
        await event_bus.publish(
            DomainEvent(
                name="crop.planted",
                tenant_id=str(self.tenant_id),
                payload={"crop_cycle_id": str(cycle.id), "crop_type": cycle.crop_type.value},
            )
        )
        return cycle

    async def get_cycle(self, cycle_id: uuid.UUID) -> CropCycle:
        return await self.cycles.get_or_404(cycle_id)

    async def list_cycles(self, *, offset: int, limit: int) -> tuple[list[CropCycle], int]:
        return await self.cycles.list(offset=offset, limit=limit), await self.cycles.count()

    async def update_cycle(self, cycle_id: uuid.UUID, data: CropCycleUpdate) -> CropCycle:
        cycle = await self.cycles.get_or_404(cycle_id)
        return await self.cycles.update(cycle, **data.model_dump(exclude_unset=True))

    async def delete_cycle(self, cycle_id: uuid.UUID) -> None:
        cycle = await self.cycles.get_or_404(cycle_id)
        await self.cycles.delete(cycle)

    # ---- inputs / harvests ----
    async def add_input(self, cycle_id: uuid.UUID, data: CropInputCreate) -> CropInput:
        await self.cycles.get_or_404(cycle_id)
        return await self.inputs.create(crop_cycle_id=cycle_id, **data.model_dump())

    async def list_inputs(self, cycle_id: uuid.UUID) -> list[CropInput]:
        return await self.inputs.list(crop_cycle_id=cycle_id, limit=500)

    async def update_input(self, input_id: uuid.UUID, data) -> CropInput:
        obj = await self.inputs.get_or_404(input_id)
        return await self.inputs.update(obj, **data.model_dump(exclude_unset=True))

    async def delete_input(self, input_id: uuid.UUID) -> None:
        await self.inputs.delete(await self.inputs.get_or_404(input_id))

    async def update_harvest(self, harvest_id: uuid.UUID, data) -> Harvest:
        obj = await self.harvests.get_or_404(harvest_id)
        return await self.harvests.update(obj, **data.model_dump(exclude_unset=True))

    async def delete_harvest(self, harvest_id: uuid.UUID) -> None:
        await self.harvests.delete(await self.harvests.get_or_404(harvest_id))

    async def list_activities(self, *, offset: int, limit: int):
        return await self.activities.list(offset=offset, limit=limit), await self.activities.count()

    async def update_activity(self, activity_id: uuid.UUID, data) -> Activity:
        obj = await self.activities.get_or_404(activity_id)
        return await self.activities.update(obj, **data.model_dump(exclude_unset=True))

    async def delete_activity(self, activity_id: uuid.UUID) -> None:
        await self.activities.delete(await self.activities.get_or_404(activity_id))

    async def add_harvest(self, cycle_id: uuid.UUID, data: HarvestCreate) -> Harvest:
        await self.cycles.get_or_404(cycle_id)
        harvest = await self.harvests.create(crop_cycle_id=cycle_id, **data.model_dump())
        await event_bus.publish(
            DomainEvent(
                name="crop.harvested",
                tenant_id=str(self.tenant_id),
                payload={"crop_cycle_id": str(cycle_id), "quantity": harvest.quantity},
            )
        )
        # Capture a structured yield example for AI learning (best-effort).
        try:
            from app.datasets.service import DatasetService

            await DatasetService(self.session, self.tenant_id).capture_yield(cycle_id)
        except Exception:  # noqa: BLE001 — never block the harvest on capture
            pass
        return harvest

    async def list_harvests(self, cycle_id: uuid.UUID) -> list[Harvest]:
        return await self.harvests.list(crop_cycle_id=cycle_id, limit=500)

    # ---- activities ----
    async def log_activity(self, data: ActivityCreate, *, created_by: uuid.UUID | None = None) -> Activity:
        return await self.activities.create(created_by=created_by, **data.model_dump())

    # ---- timeline ----
    async def timeline(self, cycle_id: uuid.UUID) -> CropTimeline:
        cycle = await self.cycles.get_or_404(cycle_id)
        events: list[TimelineEvent] = []

        if cycle.planting_date:
            events.append(
                TimelineEvent(
                    date=cycle.planting_date,
                    kind="planting",
                    title=f"Planted {cycle.crop_type.value}",
                    detail=f"{cycle.area_ha} ha, variety {cycle.variety or 'n/a'}",
                )
            )
        for inp in await self.list_inputs(cycle_id):
            events.append(
                TimelineEvent(
                    date=inp.applied_date,
                    kind="input",
                    title=f"{inp.type.value}: {inp.name}",
                    detail=f"{inp.quantity or ''} {inp.unit or ''}".strip(),
                )
            )
        for h in await self.list_harvests(cycle_id):
            events.append(
                TimelineEvent(
                    date=h.harvest_date,
                    kind="harvest",
                    title=f"Harvest {h.quantity} {h.unit}",
                    detail=f"grade {h.quality_grade}" if h.quality_grade else None,
                )
            )
        for act in await self.activities.list(crop_cycle_id=cycle_id, limit=500):
            events.append(
                TimelineEvent(
                    date=act.activity_date,
                    kind="activity",
                    title=act.type,
                    detail=act.description,
                )
            )

        events.sort(key=lambda e: (e.date is None, e.date))
        return CropTimeline(crop_cycle_id=cycle.id, crop_type=cycle.crop_type, events=events)
