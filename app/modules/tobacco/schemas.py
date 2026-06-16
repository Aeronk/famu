from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.shared.schemas import ORMModel


class TobaccoCycleCreate(BaseModel):
    farm_id: uuid.UUID
    variety: str | None = None
    season: str | None = None
    seedbed_date: date | None = None
    transplant_date: date | None = None
    area_ha: float = Field(default=0, ge=0)
    status: str = "growing"
    notes: str | None = None


class TobaccoCycleOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    farm_id: uuid.UUID
    variety: str | None
    season: str | None
    seedbed_date: date | None
    transplant_date: date | None
    area_ha: float
    status: str
    notes: str | None
    created_at: datetime


class ReapingCreate(BaseModel):
    reap_date: date | None = None
    mass_kg: float = Field(ge=0)
    bundles: int | None = None


class CuringCreate(BaseModel):
    barn: str | None = None
    method: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    mass_kg: float = Field(default=0, ge=0)


class GradingCreate(BaseModel):
    grade: str
    mass_kg: float = Field(ge=0)
    bales: int | None = None


class DeliveryCreate(BaseModel):
    floor: str | None = None
    delivery_date: date | None = None
    mass_kg: float = Field(ge=0)
    price_per_kg: float = Field(ge=0)
    deductions: float = Field(default=0, ge=0)


class ReapingOut(ORMModel):
    id: uuid.UUID
    tobacco_cycle_id: uuid.UUID
    reap_date: date | None
    mass_kg: float
    bundles: int | None


class CuringOut(ORMModel):
    id: uuid.UUID
    tobacco_cycle_id: uuid.UUID
    barn: str | None
    method: str | None
    start_date: date | None
    end_date: date | None
    mass_kg: float


class GradingOut(ORMModel):
    id: uuid.UUID
    tobacco_cycle_id: uuid.UUID
    grade: str
    mass_kg: float
    bales: int | None


class DeliveryOut(ORMModel):
    id: uuid.UUID
    tobacco_cycle_id: uuid.UUID
    floor: str | None
    delivery_date: date | None
    mass_kg: float
    price_per_kg: float
    gross_value: float
    deductions: float
    net_value: float


class ProfitabilityReport(BaseModel):
    tobacco_cycle_id: uuid.UUID
    area_ha: float
    total_reaped_kg: float
    total_cured_kg: float
    total_graded_kg: float
    total_delivered_kg: float
    gross_revenue: float
    deductions: float
    net_revenue: float
    avg_price_per_kg: float
    curing_efficiency: float          # cured / reaped
    delivery_efficiency: float        # delivered / cured
    yield_per_ha_kg: float
    estimated_costs: float
    profit: float
    margin_pct: float
