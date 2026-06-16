from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, DbSession, Pagination, require_perm
from app.modules.market.schemas import LatestPrice, MarketPriceCreate, MarketPriceOut
from app.modules.market.service import MarketService
from app.shared.enums import Role

router = APIRouter(prefix="/market", tags=["market"])


@router.post("/prices", response_model=MarketPriceOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("market:create"))])
async def create_price(payload: MarketPriceCreate, user: CurrentUser, session: DbSession):
    # Super Admin creates global prices; tenant admins create tenant-scoped prices.
    tenant_id = None if user.role == Role.SUPER_ADMIN else user.tenant_id
    return await MarketService(session, user.tenant_id).create(payload, tenant_id=tenant_id)


@router.get("/prices", response_model=list[MarketPriceOut], dependencies=[Depends(require_perm("market:read"))])
async def list_prices(
    user: CurrentUser,
    session: DbSession,
    pagination: Pagination,
    commodity: str | None = Query(None),
):
    return await MarketService(session, user.tenant_id).list(
        commodity=commodity, offset=pagination.offset, limit=pagination.limit
    )


@router.get("/prices/latest", response_model=list[LatestPrice], dependencies=[Depends(require_perm("market:read"))])
async def latest_prices(user: CurrentUser, session: DbSession):
    return await MarketService(session, user.tenant_id).latest()
