from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import DomainEvent, event_bus
from app.modules.livestock.models import (
    BreedingRecord,
    DiseaseEvent,
    Livestock,
    Vaccination,
)
from app.modules.livestock.repository import (
    BreedingRecordRepo,
    DiseaseEventRepo,
    FeedRecordRepo,
    LivestockRepo,
    VaccinationRepo,
    WeightRecordRepo,
)
from app.modules.livestock.schemas import (
    BreedingRecordCreate,
    DiseaseEventCreate,
    FeedRecordCreate,
    HerdAnalytics,
    LivestockCreate,
    LivestockUpdate,
    VaccinationCreate,
    WeightRecordCreate,
)


class LivestockService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.animals = LivestockRepo(session, tenant_id)
        self.vaccinations = VaccinationRepo(session, tenant_id)
        self.diseases = DiseaseEventRepo(session, tenant_id)
        self.weights = WeightRecordRepo(session, tenant_id)
        self.breeding = BreedingRecordRepo(session, tenant_id)
        self.feed = FeedRecordRepo(session, tenant_id)

    # ---- animals ----
    async def create(self, data: LivestockCreate) -> Livestock:
        return await self.animals.create(**data.model_dump())

    async def get(self, animal_id: uuid.UUID) -> Livestock:
        return await self.animals.get_or_404(animal_id)

    async def list(self, *, offset: int, limit: int):
        return await self.animals.list(offset=offset, limit=limit), await self.animals.count()

    async def update(self, animal_id: uuid.UUID, data: LivestockUpdate) -> Livestock:
        animal = await self.animals.get_or_404(animal_id)
        return await self.animals.update(animal, **data.model_dump(exclude_unset=True))

    async def delete(self, animal_id: uuid.UUID) -> None:
        animal = await self.animals.get_or_404(animal_id)
        await self.animals.delete(animal)

    # ---- events ----
    async def add_vaccination(self, data: VaccinationCreate) -> Vaccination:
        vac = await self.vaccinations.create(**data.model_dump())
        await event_bus.publish(
            DomainEvent(
                name="livestock.vaccinated",
                tenant_id=str(self.tenant_id),
                payload={"vaccination_id": str(vac.id), "head_count": vac.head_count},
            )
        )
        return vac

    async def add_disease(self, data: DiseaseEventCreate) -> DiseaseEvent:
        event = await self.diseases.create(**data.model_dump())
        await event_bus.publish(
            DomainEvent(
                name="livestock.disease_reported",
                tenant_id=str(self.tenant_id),
                payload={"disease": event.disease, "head_count": event.head_count},
            )
        )
        return event

    async def add_weight(self, animal_id: uuid.UUID, data: WeightRecordCreate):
        await self.animals.get_or_404(animal_id)
        rec = await self.weights.create(livestock_id=animal_id, **data.model_dump())
        animal = await self.animals.get(animal_id)
        if animal:
            animal.weight_kg = data.weight_kg
        return rec

    async def add_breeding(self, data: BreedingRecordCreate):
        return await self.breeding.create(**data.model_dump())

    async def add_feed(self, data: FeedRecordCreate):
        return await self.feed.create(**data.model_dump())

    # ---- analytics ----
    async def herd_analytics(self) -> HerdAnalytics:
        tid = str(self.tenant_id)
        today = date.today()

        async def grouped(column):
            stmt = (
                select(column, func.count())
                .where(Livestock.tenant_id == tid)
                .group_by(column)
            )
            rows = (await self.session.execute(stmt)).all()
            return {str(k): int(v) for k, v in rows if k is not None}

        by_species = await grouped(Livestock.species)
        by_status = await grouped(Livestock.status)
        by_sex = await grouped(Livestock.sex)

        totals = (
            await self.session.execute(
                select(func.count(), func.coalesce(func.sum(Livestock.weight_kg), 0)).where(
                    Livestock.tenant_id == tid
                )
            )
        ).one()
        total_head, total_weight = int(totals[0]), float(totals[1] or 0)

        vac_due = (
            await self.session.execute(
                select(func.count()).where(
                    Vaccination.tenant_id == tid,
                    Vaccination.next_due_date.isnot(None),
                    Vaccination.next_due_date <= today + timedelta(days=30),
                    Vaccination.next_due_date >= today,
                )
            )
        ).scalar_one()

        disease_recent = (
            await self.session.execute(
                select(func.count()).where(
                    DiseaseEvent.tenant_id == tid,
                    DiseaseEvent.diagnosed_date >= today - timedelta(days=90),
                )
            )
        ).scalar_one()

        births = (
            await self.session.execute(
                select(func.count()).where(
                    BreedingRecord.tenant_id == tid,
                    BreedingRecord.expected_birth_date.isnot(None),
                    BreedingRecord.actual_birth_date.is_(None),
                    BreedingRecord.expected_birth_date <= today + timedelta(days=60),
                )
            )
        ).scalar_one()

        return HerdAnalytics(
            total_head=total_head,
            by_species=by_species,
            by_status=by_status,
            by_sex=by_sex,
            total_weight_kg=round(total_weight, 2),
            average_weight_kg=round(total_weight / total_head, 2) if total_head else 0.0,
            vaccinations_due_30d=int(vac_due),
            disease_events_90d=int(disease_recent),
            expected_births_60d=int(births),
        )
