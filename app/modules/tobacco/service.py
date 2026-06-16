from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tobacco.models import TobaccoCycle
from app.modules.tobacco.repository import (
    CuringRepo,
    DeliveryRepo,
    GradingRepo,
    ReapingRepo,
    TobaccoCycleRepo,
)
from app.modules.tobacco.schemas import (
    CuringCreate,
    DeliveryCreate,
    GradingCreate,
    ProfitabilityReport,
    ReapingCreate,
    TobaccoCycleCreate,
)


def _safe_div(a: float, b: float) -> float:
    return round(a / b, 3) if b else 0.0


class TobaccoService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.tenant_id = tenant_id
        self.cycles = TobaccoCycleRepo(session, tenant_id)
        self.reaping = ReapingRepo(session, tenant_id)
        self.curing = CuringRepo(session, tenant_id)
        self.grading = GradingRepo(session, tenant_id)
        self.deliveries = DeliveryRepo(session, tenant_id)

    async def create_cycle(self, data: TobaccoCycleCreate) -> TobaccoCycle:
        return await self.cycles.create(**data.model_dump())

    async def get_cycle(self, cycle_id: uuid.UUID) -> TobaccoCycle:
        return await self.cycles.get_or_404(cycle_id)

    async def list_cycles(self, *, offset: int, limit: int):
        return await self.cycles.list(offset=offset, limit=limit), await self.cycles.count()

    async def add_reaping(self, cycle_id: uuid.UUID, data: ReapingCreate):
        await self.cycles.get_or_404(cycle_id)
        return await self.reaping.create(tobacco_cycle_id=cycle_id, **data.model_dump())

    async def add_curing(self, cycle_id: uuid.UUID, data: CuringCreate):
        await self.cycles.get_or_404(cycle_id)
        return await self.curing.create(tobacco_cycle_id=cycle_id, **data.model_dump())

    async def add_grading(self, cycle_id: uuid.UUID, data: GradingCreate):
        await self.cycles.get_or_404(cycle_id)
        return await self.grading.create(tobacco_cycle_id=cycle_id, **data.model_dump())

    async def add_delivery(self, cycle_id: uuid.UUID, data: DeliveryCreate):
        await self.cycles.get_or_404(cycle_id)
        gross = round(data.mass_kg * data.price_per_kg, 2)
        net = round(gross - data.deductions, 2)
        return await self.deliveries.create(
            tobacco_cycle_id=cycle_id,
            floor=data.floor,
            delivery_date=data.delivery_date,
            mass_kg=data.mass_kg,
            price_per_kg=data.price_per_kg,
            gross_value=gross,
            deductions=data.deductions,
            net_value=net,
        )

    async def profitability(
        self, cycle_id: uuid.UUID, *, estimated_costs: float = 0.0
    ) -> ProfitabilityReport:
        cycle = await self.cycles.get_or_404(cycle_id)
        reaping = await self.reaping.list(tobacco_cycle_id=cycle_id, limit=1000)
        curing = await self.curing.list(tobacco_cycle_id=cycle_id, limit=1000)
        grading = await self.grading.list(tobacco_cycle_id=cycle_id, limit=1000)
        deliveries = await self.deliveries.list(tobacco_cycle_id=cycle_id, limit=1000)

        reaped = sum(r.mass_kg for r in reaping)
        cured = sum(c.mass_kg for c in curing)
        graded = sum(g.mass_kg for g in grading)
        delivered = sum(float(d.mass_kg) for d in deliveries)
        gross = sum(float(d.gross_value) for d in deliveries)
        deductions = sum(float(d.deductions) for d in deliveries)
        net = sum(float(d.net_value) for d in deliveries)
        profit = round(net - estimated_costs, 2)

        return ProfitabilityReport(
            tobacco_cycle_id=cycle.id,
            area_ha=cycle.area_ha,
            total_reaped_kg=round(reaped, 2),
            total_cured_kg=round(cured, 2),
            total_graded_kg=round(graded, 2),
            total_delivered_kg=round(delivered, 2),
            gross_revenue=round(gross, 2),
            deductions=round(deductions, 2),
            net_revenue=round(net, 2),
            avg_price_per_kg=_safe_div(gross, delivered),
            curing_efficiency=_safe_div(cured, reaped),
            delivery_efficiency=_safe_div(delivered, cured),
            yield_per_ha_kg=_safe_div(delivered, cycle.area_ha),
            estimated_costs=round(estimated_costs, 2),
            profit=profit,
            margin_pct=round(_safe_div(profit, net) * 100, 2),
        )
