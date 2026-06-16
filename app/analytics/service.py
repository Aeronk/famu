from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.crops.models import CropCycle, Harvest
from app.modules.farms.models import Farm
from app.modules.finance.models import Expense, Income
from app.modules.finance.service import FinanceService
from app.modules.livestock.models import Livestock
from app.modules.livestock.service import LivestockService
from app.modules.weather.models import WeatherAlert, WeatherRecord
from app.shared.enums import CropCycleStatus


class AnalyticsService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.tid = str(tenant_id)

    async def _scalar(self, stmt) -> float:
        return float((await self.session.execute(stmt)).scalar_one() or 0)

    async def overview(self) -> dict:
        farms = await self._scalar(
            select(func.count()).select_from(Farm).where(Farm.tenant_id == self.tid)
        )
        active_cycles = await self._scalar(
            select(func.count()).select_from(CropCycle).where(
                CropCycle.tenant_id == self.tid,
                CropCycle.status.in_([CropCycleStatus.PLANTED, CropCycleStatus.GROWING]),
            )
        )
        head = await self._scalar(
            select(func.count()).select_from(Livestock).where(Livestock.tenant_id == self.tid)
        )
        income = await self._scalar(
            select(func.coalesce(func.sum(Income.amount), 0)).where(Income.tenant_id == self.tid)
        )
        expense = await self._scalar(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.tenant_id == self.tid)
        )
        alerts = await self._scalar(
            select(func.count()).select_from(WeatherAlert).where(WeatherAlert.tenant_id == self.tid)
        )
        return {
            "farms": int(farms),
            "active_crop_cycles": int(active_cycles),
            "livestock_head": int(head),
            "total_income": round(income, 2),
            "total_expense": round(expense, 2),
            "net_position": round(income - expense, 2),
            "weather_alerts": int(alerts),
        }

    async def yields(self) -> dict:
        stmt = (
            select(
                CropCycle.crop_type,
                func.coalesce(func.sum(Harvest.quantity), 0),
                func.coalesce(func.sum(CropCycle.area_ha), 0),
                func.count(func.distinct(CropCycle.id)),
            )
            .join(Harvest, Harvest.crop_cycle_id == CropCycle.id, isouter=True)
            .where(CropCycle.tenant_id == self.tid)
            .group_by(CropCycle.crop_type)
        )
        rows = (await self.session.execute(stmt)).all()
        by_crop = []
        for crop_type, harvest_qty, area, cycles in rows:
            area = float(area or 0)
            qty = float(harvest_qty or 0)
            by_crop.append(
                {
                    "crop": crop_type.value if crop_type else "unknown",
                    "cycles": int(cycles),
                    "total_harvest": round(qty, 2),
                    "total_area_ha": round(area, 2),
                    "yield_per_ha": round(qty / area, 2) if area else 0.0,
                }
            )
        return {"by_crop": by_crop}

    async def weather(self) -> dict:
        latest = (
            await self.session.execute(
                select(WeatherRecord)
                .where(WeatherRecord.tenant_id == self.tid)
                .order_by(WeatherRecord.observed_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        severity_rows = (
            await self.session.execute(
                select(WeatherAlert.severity, func.count())
                .where(WeatherAlert.tenant_id == self.tid)
                .group_by(WeatherAlert.severity)
            )
        ).all()
        return {
            "latest": (
                {
                    "observed_at": latest.observed_at.isoformat(),
                    "rainfall_mm": latest.rainfall_mm,
                    "temp_c": latest.temp_c,
                    "humidity": latest.humidity,
                    "wind_kph": latest.wind_kph,
                    "source": latest.source,
                }
                if latest
                else None
            ),
            "alerts_by_severity": {str(s): int(c) for s, c in severity_rows},
        }

    async def finances(self) -> dict:
        svc = FinanceService(self.session, self.tenant_id)
        profitability = await svc.profitability()
        cashflow = await svc.cashflow()
        return {
            "profitability": profitability.model_dump(),
            "recent_cashflow": [p.model_dump() for p in cashflow.periods[-6:]],
        }

    async def livestock(self) -> dict:
        analytics = await LivestockService(self.session, self.tenant_id).herd_analytics()
        return analytics.model_dump()
