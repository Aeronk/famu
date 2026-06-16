from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import DbSession, Pagination, TenantId, require_perm
from app.modules.crops.schemas import (
    ActivityCreate,
    ActivityOut,
    CropCycleCreate,
    CropCycleOut,
    CropCycleUpdate,
    CropInputCreate,
    CropInputOut,
    CropTimeline,
    HarvestCreate,
    HarvestOut,
)
from app.modules.crops.service import CropService
from app.shared.schemas import Message, Page

router = APIRouter(prefix="/crops", tags=["crops"])


@router.post("/cycles", response_model=CropCycleOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("crop:create"))])
async def create_cycle(payload: CropCycleCreate, session: DbSession, tenant_id: TenantId):
    return await CropService(session, tenant_id).create_cycle(payload)


@router.get("/cycles", response_model=Page[CropCycleOut], dependencies=[Depends(require_perm("crop:read"))])
async def list_cycles(session: DbSession, tenant_id: TenantId, pagination: Pagination):
    items, total = await CropService(session, tenant_id).list_cycles(
        offset=pagination.offset, limit=pagination.limit
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/cycles/{cycle_id}", response_model=CropCycleOut, dependencies=[Depends(require_perm("crop:read"))])
async def get_cycle(cycle_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    return await CropService(session, tenant_id).get_cycle(cycle_id)


@router.patch("/cycles/{cycle_id}", response_model=CropCycleOut, dependencies=[Depends(require_perm("crop:update"))])
async def update_cycle(cycle_id: uuid.UUID, payload: CropCycleUpdate, session: DbSession, tenant_id: TenantId):
    return await CropService(session, tenant_id).update_cycle(cycle_id, payload)


@router.delete("/cycles/{cycle_id}", response_model=Message, dependencies=[Depends(require_perm("crop:delete"))])
async def delete_cycle(cycle_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    await CropService(session, tenant_id).delete_cycle(cycle_id)
    return Message(message="Crop cycle deleted")


@router.get("/cycles/{cycle_id}/timeline", response_model=CropTimeline, dependencies=[Depends(require_perm("crop:read"))])
async def cycle_timeline(cycle_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    return await CropService(session, tenant_id).timeline(cycle_id)


@router.post("/cycles/{cycle_id}/inputs", response_model=CropInputOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("crop:update"))])
async def add_input(cycle_id: uuid.UUID, payload: CropInputCreate, session: DbSession, tenant_id: TenantId):
    return await CropService(session, tenant_id).add_input(cycle_id, payload)


@router.get("/cycles/{cycle_id}/inputs", response_model=list[CropInputOut], dependencies=[Depends(require_perm("crop:read"))])
async def list_inputs(cycle_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    return await CropService(session, tenant_id).list_inputs(cycle_id)


@router.post("/cycles/{cycle_id}/harvests", response_model=HarvestOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("crop:update"))])
async def add_harvest(cycle_id: uuid.UUID, payload: HarvestCreate, session: DbSession, tenant_id: TenantId):
    return await CropService(session, tenant_id).add_harvest(cycle_id, payload)


@router.get("/cycles/{cycle_id}/harvests", response_model=list[HarvestOut], dependencies=[Depends(require_perm("crop:read"))])
async def list_harvests(cycle_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    return await CropService(session, tenant_id).list_harvests(cycle_id)


@router.post("/activities", response_model=ActivityOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("crop:create"))])
async def log_activity(payload: ActivityCreate, session: DbSession, tenant_id: TenantId):
    return await CropService(session, tenant_id).log_activity(payload)
