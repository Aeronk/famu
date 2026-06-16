from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import DbSession, Pagination, TenantId, require_perm
from app.modules.livestock.schemas import (
    BreedingRecordCreate,
    BreedingRecordOut,
    DiseaseEventCreate,
    DiseaseEventOut,
    FeedRecordCreate,
    FeedRecordOut,
    HerdAnalytics,
    LivestockCreate,
    LivestockOut,
    LivestockUpdate,
    VaccinationCreate,
    VaccinationOut,
    WeightRecordCreate,
    WeightRecordOut,
)
from app.modules.livestock.service import LivestockService
from app.shared.schemas import Message, Page

router = APIRouter(prefix="/livestock", tags=["livestock"])


@router.post("", response_model=LivestockOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("livestock:create"))])
async def create_animal(payload: LivestockCreate, session: DbSession, tenant_id: TenantId):
    return await LivestockService(session, tenant_id).create(payload)


@router.get("", response_model=Page[LivestockOut], dependencies=[Depends(require_perm("livestock:read"))])
async def list_animals(session: DbSession, tenant_id: TenantId, pagination: Pagination):
    items, total = await LivestockService(session, tenant_id).list(
        offset=pagination.offset, limit=pagination.limit
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/analytics", response_model=HerdAnalytics, dependencies=[Depends(require_perm("livestock:read"))])
async def herd_analytics(session: DbSession, tenant_id: TenantId):
    return await LivestockService(session, tenant_id).herd_analytics()


@router.get("/{animal_id}", response_model=LivestockOut, dependencies=[Depends(require_perm("livestock:read"))])
async def get_animal(animal_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    return await LivestockService(session, tenant_id).get(animal_id)


@router.patch("/{animal_id}", response_model=LivestockOut, dependencies=[Depends(require_perm("livestock:update"))])
async def update_animal(animal_id: uuid.UUID, payload: LivestockUpdate, session: DbSession, tenant_id: TenantId):
    return await LivestockService(session, tenant_id).update(animal_id, payload)


@router.delete("/{animal_id}", response_model=Message, dependencies=[Depends(require_perm("livestock:delete"))])
async def delete_animal(animal_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    await LivestockService(session, tenant_id).delete(animal_id)
    return Message(message="Animal removed")


@router.post("/vaccinations", response_model=VaccinationOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("livestock:update"))])
async def add_vaccination(payload: VaccinationCreate, session: DbSession, tenant_id: TenantId):
    return await LivestockService(session, tenant_id).add_vaccination(payload)


@router.post("/disease-events", response_model=DiseaseEventOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("livestock:update"))])
async def add_disease(payload: DiseaseEventCreate, session: DbSession, tenant_id: TenantId):
    return await LivestockService(session, tenant_id).add_disease(payload)


@router.post("/{animal_id}/weights", response_model=WeightRecordOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("livestock:update"))])
async def add_weight(animal_id: uuid.UUID, payload: WeightRecordCreate, session: DbSession, tenant_id: TenantId):
    return await LivestockService(session, tenant_id).add_weight(animal_id, payload)


@router.post("/breeding", response_model=BreedingRecordOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("livestock:update"))])
async def add_breeding(payload: BreedingRecordCreate, session: DbSession, tenant_id: TenantId):
    return await LivestockService(session, tenant_id).add_breeding(payload)


@router.post("/feed", response_model=FeedRecordOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("livestock:update"))])
async def add_feed(payload: FeedRecordCreate, session: DbSession, tenant_id: TenantId):
    return await LivestockService(session, tenant_id).add_feed(payload)
