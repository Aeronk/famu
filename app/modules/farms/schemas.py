from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.shared.enums import EnterpriseType, FarmingType
from app.shared.schemas import ORMModel


class FarmBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    farming_type: FarmingType = FarmingType.PERSONAL
    enterprise_type: EnterpriseType = EnterpriseType.MIXED
    gps_lat: float | None = Field(default=None, ge=-90, le=90)
    gps_lng: float | None = Field(default=None, ge=-180, le=180)
    province: str | None = None
    district: str | None = None
    ward: str | None = None
    village: str | None = None
    soil_type: str | None = None
    water_source: str | None = None
    irrigation_type: str | None = None
    size_ha: float | None = Field(default=None, ge=0)
    notes: str | None = None


class FarmCreate(FarmBase):
    owner_user_id: uuid.UUID | None = None


class FarmUpdate(BaseModel):
    name: str | None = None
    farming_type: FarmingType | None = None
    enterprise_type: EnterpriseType | None = None
    gps_lat: float | None = Field(default=None, ge=-90, le=90)
    gps_lng: float | None = Field(default=None, ge=-180, le=180)
    province: str | None = None
    district: str | None = None
    ward: str | None = None
    village: str | None = None
    soil_type: str | None = None
    water_source: str | None = None
    irrigation_type: str | None = None
    size_ha: float | None = Field(default=None, ge=0)
    notes: str | None = None
    owner_user_id: uuid.UUID | None = None


class FarmOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    farming_type: FarmingType
    enterprise_type: EnterpriseType
    owner_user_id: uuid.UUID | None
    gps_lat: float | None
    gps_lng: float | None
    province: str | None
    district: str | None
    ward: str | None
    village: str | None
    soil_type: str | None
    water_source: str | None
    irrigation_type: str | None
    size_ha: float | None
    notes: str | None
    created_at: datetime
