from __future__ import annotations

from fastapi import APIRouter, Depends

from app.analytics.service import AnalyticsService
from app.api.deps import DbSession, TenantId, require_perm

router = APIRouter(prefix="/dashboard", tags=["analytics"])


@router.get("/overview", dependencies=[Depends(require_perm("analytics:read"))])
async def overview(session: DbSession, tenant_id: TenantId):
    return await AnalyticsService(session, tenant_id).overview()


@router.get("/yields", dependencies=[Depends(require_perm("analytics:read"))])
async def yields(session: DbSession, tenant_id: TenantId):
    return await AnalyticsService(session, tenant_id).yields()


@router.get("/weather", dependencies=[Depends(require_perm("analytics:read"))])
async def weather(session: DbSession, tenant_id: TenantId):
    return await AnalyticsService(session, tenant_id).weather()


@router.get("/finances", dependencies=[Depends(require_perm("analytics:read"))])
async def finances(session: DbSession, tenant_id: TenantId):
    return await AnalyticsService(session, tenant_id).finances()


@router.get("/livestock", dependencies=[Depends(require_perm("analytics:read"))])
async def livestock(session: DbSession, tenant_id: TenantId):
    return await AnalyticsService(session, tenant_id).livestock()
