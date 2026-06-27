from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import DbSession, Pagination, TenantId, require_perm
from app.modules.livestock.schemas import (
    BreedingRecordCreate,
    BreedingRecordOut,
    DiseaseEventCreate,
    DiseaseEventOut,
    DiseaseEventUpdate,
    FeedRecordCreate,
    FeedRecordOut,
    HerdAnalytics,
    LivestockCreate,
    LivestockOut,
    LivestockUpdate,
    VaccinationCreate,
    VaccinationOut,
    VaccinationUpdate,
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


# ---- event listings (registered before /{animal_id} to avoid path capture) ----
@router.get("/vaccinations", response_model=Page[VaccinationOut], dependencies=[Depends(require_perm("livestock:read"))])
async def list_vaccinations(session: DbSession, tenant_id: TenantId, pagination: Pagination):
    items, total = await LivestockService(session, tenant_id).list_vaccinations(offset=pagination.offset, limit=pagination.limit)
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/disease-events", response_model=Page[DiseaseEventOut], dependencies=[Depends(require_perm("livestock:read"))])
async def list_diseases(session: DbSession, tenant_id: TenantId, pagination: Pagination):
    items, total = await LivestockService(session, tenant_id).list_diseases(offset=pagination.offset, limit=pagination.limit)
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/breeding", response_model=Page[BreedingRecordOut], dependencies=[Depends(require_perm("livestock:read"))])
async def list_breeding(session: DbSession, tenant_id: TenantId, pagination: Pagination):
    items, total = await LivestockService(session, tenant_id).list_breeding(offset=pagination.offset, limit=pagination.limit)
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/feed", response_model=Page[FeedRecordOut], dependencies=[Depends(require_perm("livestock:read"))])
async def list_feed(session: DbSession, tenant_id: TenantId, pagination: Pagination):
    items, total = await LivestockService(session, tenant_id).list_feed(offset=pagination.offset, limit=pagination.limit)
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


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


# ---- event update / delete (full CRUD) ----
@router.patch("/vaccinations/{vac_id}", response_model=VaccinationOut, dependencies=[Depends(require_perm("livestock:update"))])
async def update_vaccination(vac_id: uuid.UUID, payload: VaccinationUpdate, session: DbSession, tenant_id: TenantId):
    return await LivestockService(session, tenant_id).update_vaccination(vac_id, payload)


@router.delete("/vaccinations/{vac_id}", response_model=Message, dependencies=[Depends(require_perm("livestock:delete"))])
async def delete_vaccination(vac_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    await LivestockService(session, tenant_id).delete_vaccination(vac_id)
    return Message(message="Vaccination deleted")


@router.patch("/disease-events/{event_id}", response_model=DiseaseEventOut, dependencies=[Depends(require_perm("livestock:update"))])
async def update_disease(event_id: uuid.UUID, payload: DiseaseEventUpdate, session: DbSession, tenant_id: TenantId):
    return await LivestockService(session, tenant_id).update_disease(event_id, payload)


@router.delete("/disease-events/{event_id}", response_model=Message, dependencies=[Depends(require_perm("livestock:delete"))])
async def delete_disease(event_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    await LivestockService(session, tenant_id).delete_disease(event_id)
    return Message(message="Disease event deleted")


@router.get("/{animal_id}/weights", response_model=list[WeightRecordOut], dependencies=[Depends(require_perm("livestock:read"))])
async def list_weights(animal_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    return await LivestockService(session, tenant_id).list_weights(animal_id)


@router.delete("/weights/{weight_id}", response_model=Message, dependencies=[Depends(require_perm("livestock:delete"))])
async def delete_weight(weight_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    await LivestockService(session, tenant_id).delete_weight(weight_id)
    return Message(message="Weight record deleted")


@router.delete("/breeding/{breeding_id}", response_model=Message, dependencies=[Depends(require_perm("livestock:delete"))])
async def delete_breeding(breeding_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    await LivestockService(session, tenant_id).delete_breeding(breeding_id)
    return Message(message="Breeding record deleted")


@router.delete("/feed/{feed_id}", response_model=Message, dependencies=[Depends(require_perm("livestock:delete"))])
async def delete_feed(feed_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    await LivestockService(session, tenant_id).delete_feed(feed_id)
    return Message(message="Feed record deleted")
