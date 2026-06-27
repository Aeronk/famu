from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.market.models import MarketPrice
from app.modules.market.schemas import LatestPrice, MarketPriceCreate
from app.shared.exceptions import NotFoundError


class MarketService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID | None = None):
        self.session = session
        self.tenant_id = tenant_id

    def _visible(self, stmt):
        if self.tenant_id is None:
            return stmt
        return stmt.where(
            or_(MarketPrice.tenant_id.is_(None), MarketPrice.tenant_id == str(self.tenant_id))
        )

    async def create(self, data: MarketPriceCreate, *, tenant_id: uuid.UUID | None) -> MarketPrice:
        price = MarketPrice(tenant_id=tenant_id, **data.model_dump())
        self.session.add(price)
        await self.session.flush()
        return price

    async def list(self, *, commodity: str | None, offset: int, limit: int) -> list[MarketPrice]:
        stmt = self._visible(select(MarketPrice))
        if commodity:
            stmt = stmt.where(MarketPrice.commodity == commodity)
        stmt = stmt.order_by(MarketPrice.price_date.desc().nullslast()).offset(offset).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def latest(self) -> list[LatestPrice]:
        rows = list((await self.session.execute(self._visible(select(MarketPrice)))).scalars().all())
        latest: dict[str, MarketPrice] = {}
        for row in rows:
            cur = latest.get(row.commodity)
            if cur is None or (row.price_date or row.created_at.date()) >= (
                cur.price_date or cur.created_at.date()
            ):
                latest[row.commodity] = row
        return [
            LatestPrice(
                commodity=r.commodity,
                price=float(r.price),
                currency=r.currency,
                unit=r.unit,
                market=r.market,
                price_date=r.price_date,
            )
            for r in sorted(latest.values(), key=lambda x: x.commodity)
        ]

    async def _owned(self, price_id) -> MarketPrice:
        stmt = select(MarketPrice).where(
            MarketPrice.id == price_id, MarketPrice.tenant_id == str(self.tenant_id)
        )
        price = (await self.session.execute(stmt)).scalar_one_or_none()
        if not price:
            raise NotFoundError("Market price not found")
        return price

    async def update(self, price_id, data) -> MarketPrice:
        price = await self._owned(price_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(price, k, v)
        await self.session.flush()
        return price

    async def delete(self, price_id) -> None:
        price = await self._owned(price_id)
        await self.session.delete(price)
        await self.session.flush()

    async def latest_price_for(self, commodity: str) -> float | None:
        for lp in await self.latest():
            if lp.commodity.lower() == commodity.lower():
                return lp.price
        return None
