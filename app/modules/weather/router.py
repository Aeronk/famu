from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import DbSession, Pagination, TenantId, require_perm
from app.modules.weather.schemas import (
    WeatherAlertOut,
    WeatherRecordOut,
    WeatherSyncRequest,
)
from app.modules.weather.service import WeatherService
from app.shared.schemas import Page

router = APIRouter(prefix="/weather", tags=["weather"])


@router.post("/sync", response_model=WeatherRecordOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("weather:read"))])
async def sync_weather(payload: WeatherSyncRequest, session: DbSession, tenant_id: TenantId):
    return await WeatherService(session, tenant_id).sync(payload)


@router.get("/records", response_model=Page[WeatherRecordOut], dependencies=[Depends(require_perm("weather:read"))])
async def list_records(session: DbSession, tenant_id: TenantId, pagination: Pagination):
    items, total = await WeatherService(session, tenant_id).list_records(
        offset=pagination.offset, limit=pagination.limit
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/alerts", response_model=Page[WeatherAlertOut], dependencies=[Depends(require_perm("weather:read"))])
async def list_alerts(session: DbSession, tenant_id: TenantId, pagination: Pagination):
    items, total = await WeatherService(session, tenant_id).list_alerts(
        offset=pagination.offset, limit=pagination.limit
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)
