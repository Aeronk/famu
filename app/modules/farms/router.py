from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import DbSession, Pagination, TenantId, require_perm
from app.modules.farms.schemas import FarmCreate, FarmOut, FarmUpdate
from app.modules.farms.service import FarmService
from app.shared.schemas import Message, Page

router = APIRouter(prefix="/farms", tags=["farms"])


@router.post("", response_model=FarmOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("farm:create"))])
async def create_farm(payload: FarmCreate, session: DbSession, tenant_id: TenantId):
    return await FarmService(session, tenant_id).create(payload)


@router.get("", response_model=Page[FarmOut], dependencies=[Depends(require_perm("farm:read"))])
async def list_farms(session: DbSession, tenant_id: TenantId, pagination: Pagination):
    items, total = await FarmService(session, tenant_id).list(
        offset=pagination.offset, limit=pagination.limit
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/{farm_id}", response_model=FarmOut, dependencies=[Depends(require_perm("farm:read"))])
async def get_farm(farm_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    return await FarmService(session, tenant_id).get(farm_id)


@router.patch("/{farm_id}", response_model=FarmOut, dependencies=[Depends(require_perm("farm:update"))])
async def update_farm(farm_id: uuid.UUID, payload: FarmUpdate, session: DbSession, tenant_id: TenantId):
    return await FarmService(session, tenant_id).update(farm_id, payload)


@router.delete("/{farm_id}", response_model=Message, dependencies=[Depends(require_perm("farm:delete"))])
async def delete_farm(farm_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    await FarmService(session, tenant_id).delete(farm_id)
    return Message(message="Farm deleted")
