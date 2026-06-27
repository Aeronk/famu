from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession, Pagination, TenantId, require_perm
from app.modules.tobacco.schemas import (
    CuringCreate,
    CuringOut,
    DeliveryCreate,
    DeliveryOut,
    GradingCreate,
    GradingOut,
    ProfitabilityReport,
    ReapingCreate,
    ReapingOut,
    TobaccoCycleCreate,
    TobaccoCycleOut,
)
from app.modules.tobacco.service import TobaccoService
from app.shared.schemas import Message, Page

router = APIRouter(prefix="/tobacco", tags=["tobacco"])


@router.post("/cycles", response_model=TobaccoCycleOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("tobacco:create"))])
async def create_cycle(payload: TobaccoCycleCreate, session: DbSession, tenant_id: TenantId):
    return await TobaccoService(session, tenant_id).create_cycle(payload)


@router.get("/cycles", response_model=Page[TobaccoCycleOut], dependencies=[Depends(require_perm("tobacco:read"))])
async def list_cycles(session: DbSession, tenant_id: TenantId, pagination: Pagination):
    items, total = await TobaccoService(session, tenant_id).list_cycles(
        offset=pagination.offset, limit=pagination.limit
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/cycles/{cycle_id}", response_model=TobaccoCycleOut, dependencies=[Depends(require_perm("tobacco:read"))])
async def get_cycle(cycle_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    return await TobaccoService(session, tenant_id).get_cycle(cycle_id)


@router.post("/cycles/{cycle_id}/reaping", response_model=ReapingOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("tobacco:update"))])
async def add_reaping(cycle_id: uuid.UUID, payload: ReapingCreate, session: DbSession, tenant_id: TenantId):
    return await TobaccoService(session, tenant_id).add_reaping(cycle_id, payload)


@router.post("/cycles/{cycle_id}/curing", response_model=CuringOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("tobacco:update"))])
async def add_curing(cycle_id: uuid.UUID, payload: CuringCreate, session: DbSession, tenant_id: TenantId):
    return await TobaccoService(session, tenant_id).add_curing(cycle_id, payload)


@router.post("/cycles/{cycle_id}/grading", response_model=GradingOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("tobacco:update"))])
async def add_grading(cycle_id: uuid.UUID, payload: GradingCreate, session: DbSession, tenant_id: TenantId):
    return await TobaccoService(session, tenant_id).add_grading(cycle_id, payload)


@router.post("/cycles/{cycle_id}/deliveries", response_model=DeliveryOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("tobacco:update"))])
async def add_delivery(cycle_id: uuid.UUID, payload: DeliveryCreate, session: DbSession, tenant_id: TenantId):
    return await TobaccoService(session, tenant_id).add_delivery(cycle_id, payload)


@router.get("/cycles/{cycle_id}/reaping", response_model=list[ReapingOut], dependencies=[Depends(require_perm("tobacco:read"))])
async def list_reaping(cycle_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    return await TobaccoService(session, tenant_id).list_reaping(cycle_id)


@router.get("/cycles/{cycle_id}/curing", response_model=list[CuringOut], dependencies=[Depends(require_perm("tobacco:read"))])
async def list_curing(cycle_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    return await TobaccoService(session, tenant_id).list_curing(cycle_id)


@router.get("/cycles/{cycle_id}/grading", response_model=list[GradingOut], dependencies=[Depends(require_perm("tobacco:read"))])
async def list_grading(cycle_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    return await TobaccoService(session, tenant_id).list_grading(cycle_id)


@router.get("/cycles/{cycle_id}/deliveries", response_model=list[DeliveryOut], dependencies=[Depends(require_perm("tobacco:read"))])
async def list_deliveries(cycle_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    return await TobaccoService(session, tenant_id).list_deliveries(cycle_id)


@router.delete("/reaping/{rid}", response_model=Message, dependencies=[Depends(require_perm("tobacco:delete"))])
async def delete_reaping(rid: uuid.UUID, session: DbSession, tenant_id: TenantId):
    await TobaccoService(session, tenant_id).delete_reaping(rid)
    return Message(message="Reaping record deleted")


@router.delete("/curing/{cid}", response_model=Message, dependencies=[Depends(require_perm("tobacco:delete"))])
async def delete_curing(cid: uuid.UUID, session: DbSession, tenant_id: TenantId):
    await TobaccoService(session, tenant_id).delete_curing(cid)
    return Message(message="Curing record deleted")


@router.delete("/grading/{gid}", response_model=Message, dependencies=[Depends(require_perm("tobacco:delete"))])
async def delete_grading(gid: uuid.UUID, session: DbSession, tenant_id: TenantId):
    await TobaccoService(session, tenant_id).delete_grading(gid)
    return Message(message="Grading record deleted")


@router.delete("/deliveries/{did}", response_model=Message, dependencies=[Depends(require_perm("tobacco:delete"))])
async def delete_delivery(did: uuid.UUID, session: DbSession, tenant_id: TenantId):
    await TobaccoService(session, tenant_id).delete_delivery(did)
    return Message(message="Delivery record deleted")


@router.get("/cycles/{cycle_id}/profitability", response_model=ProfitabilityReport, dependencies=[Depends(require_perm("tobacco:read"))])
async def profitability(
    cycle_id: uuid.UUID,
    session: DbSession,
    tenant_id: TenantId,
    estimated_costs: float = Query(0.0, ge=0),
):
    return await TobaccoService(session, tenant_id).profitability(
        cycle_id, estimated_costs=estimated_costs
    )
