from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.shared.enums import ActivitySource, CropCycleStatus, CropType, InputType
from app.shared.schemas import ORMModel


# ---- Crop cycle ----
class CropCycleCreate(BaseModel):
    farm_id: uuid.UUID
    crop_type: CropType
    variety: str | None = None
    season: str | None = None
    planting_date: date | None = None
    expected_harvest_date: date | None = None
    area_ha: float = Field(default=0, ge=0)
    status: CropCycleStatus = CropCycleStatus.PLANNED
    notes: str | None = None


class CropCycleUpdate(BaseModel):
    crop_type: CropType | None = None
    variety: str | None = None
    season: str | None = None
    planting_date: date | None = None
    expected_harvest_date: date | None = None
    area_ha: float | None = Field(default=None, ge=0)
    status: CropCycleStatus | None = None
    notes: str | None = None


class CropCycleOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    farm_id: uuid.UUID
    crop_type: CropType
    variety: str | None
    season: str | None
    planting_date: date | None
    expected_harvest_date: date | None
    area_ha: float
    status: CropCycleStatus
    notes: str | None
    created_at: datetime


# ---- Crop input ----
class CropInputCreate(BaseModel):
    type: InputType
    name: str
    quantity: float | None = None
    unit: str | None = None
    cost: float | None = Field(default=None, ge=0)
    applied_date: date | None = None


class CropInputOut(ORMModel):
    id: uuid.UUID
    crop_cycle_id: uuid.UUID
    type: InputType
    name: str
    quantity: float | None
    unit: str | None
    cost: float | None
    applied_date: date | None


# ---- Harvest ----
class HarvestCreate(BaseModel):
    harvest_date: date | None = None
    quantity: float = Field(ge=0)
    unit: str = "kg"
    quality_grade: str | None = None
    revenue: float | None = Field(default=None, ge=0)


class HarvestOut(ORMModel):
    id: uuid.UUID
    crop_cycle_id: uuid.UUID
    harvest_date: date | None
    quantity: float
    unit: str
    quality_grade: str | None
    revenue: float | None


# ---- Activity ----
class ActivityCreate(BaseModel):
    farm_id: uuid.UUID | None = None
    crop_cycle_id: uuid.UUID | None = None
    livestock_id: uuid.UUID | None = None
    type: str
    description: str | None = None
    activity_date: date | None = None
    source: ActivitySource = ActivitySource.MANUAL
    meta: dict = Field(default_factory=dict)


class ActivityOut(ORMModel):
    id: uuid.UUID
    farm_id: uuid.UUID | None
    crop_cycle_id: uuid.UUID | None
    livestock_id: uuid.UUID | None
    type: str
    description: str | None
    activity_date: date | None
    source: ActivitySource
    created_at: datetime


# ---- Timeline ----
class TimelineEvent(BaseModel):
    date: date | None
    kind: str  # planting | input | harvest | activity
    title: str
    detail: str | None = None


class CropTimeline(BaseModel):
    crop_cycle_id: uuid.UUID
    crop_type: CropType
    events: list[TimelineEvent]
