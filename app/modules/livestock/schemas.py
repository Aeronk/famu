from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.shared.enums import LivestockSpecies, LivestockStatus, Sex
from app.shared.schemas import ORMModel


# ---- Animal ----
class LivestockCreate(BaseModel):
    farm_id: uuid.UUID
    species: LivestockSpecies
    tag_number: str | None = None
    breed: str | None = None
    sex: Sex | None = None
    dob: date | None = None
    weight_kg: float | None = Field(default=None, ge=0)
    status: LivestockStatus = LivestockStatus.ACTIVE
    acquired_date: date | None = None
    notes: str | None = None


class LivestockUpdate(BaseModel):
    tag_number: str | None = None
    breed: str | None = None
    sex: Sex | None = None
    dob: date | None = None
    weight_kg: float | None = Field(default=None, ge=0)
    status: LivestockStatus | None = None
    notes: str | None = None


class LivestockOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    farm_id: uuid.UUID
    species: LivestockSpecies
    tag_number: str | None
    breed: str | None
    sex: Sex | None
    dob: date | None
    weight_kg: float | None
    status: LivestockStatus
    acquired_date: date | None
    created_at: datetime


# ---- Events ----
class VaccinationCreate(BaseModel):
    livestock_id: uuid.UUID | None = None
    head_count: int = Field(default=1, ge=1)
    vaccine: str | None = None
    vaccination_date: date | None = None
    dose: str | None = None
    administered_by: str | None = None
    next_due_date: date | None = None


class VaccinationOut(ORMModel):
    id: uuid.UUID
    livestock_id: uuid.UUID | None
    head_count: int
    vaccine: str | None
    vaccination_date: date | None
    dose: str | None
    administered_by: str | None
    next_due_date: date | None


class DiseaseEventCreate(BaseModel):
    livestock_id: uuid.UUID | None = None
    head_count: int = Field(default=1, ge=1)
    disease: str
    diagnosed_date: date | None = None
    treatment: str | None = None
    outcome: str | None = None


class DiseaseEventOut(ORMModel):
    id: uuid.UUID
    livestock_id: uuid.UUID | None
    head_count: int
    disease: str
    diagnosed_date: date | None
    treatment: str | None
    outcome: str | None


class WeightRecordCreate(BaseModel):
    recorded_date: date | None = None
    weight_kg: float = Field(ge=0)


class WeightRecordOut(ORMModel):
    id: uuid.UUID
    livestock_id: uuid.UUID
    recorded_date: date | None
    weight_kg: float


class BreedingRecordCreate(BaseModel):
    dam_id: uuid.UUID
    sire_id: uuid.UUID | None = None
    service_date: date | None = None
    expected_birth_date: date | None = None
    actual_birth_date: date | None = None
    offspring_count: int | None = None


class BreedingRecordOut(ORMModel):
    id: uuid.UUID
    dam_id: uuid.UUID
    sire_id: uuid.UUID | None
    service_date: date | None
    expected_birth_date: date | None
    actual_birth_date: date | None
    offspring_count: int | None


class FeedRecordCreate(BaseModel):
    livestock_id: uuid.UUID | None = None
    farm_id: uuid.UUID | None = None
    feed_type: str
    quantity: float | None = None
    unit: str | None = None
    cost: float | None = Field(default=None, ge=0)
    feed_date: date | None = None


class FeedRecordOut(ORMModel):
    id: uuid.UUID
    livestock_id: uuid.UUID | None
    farm_id: uuid.UUID | None
    feed_type: str
    quantity: float | None
    unit: str | None
    cost: float | None
    feed_date: date | None


# ---- Analytics ----
class HerdAnalytics(BaseModel):
    total_head: int
    by_species: dict[str, int]
    by_status: dict[str, int]
    by_sex: dict[str, int]
    total_weight_kg: float
    average_weight_kg: float
    vaccinations_due_30d: int
    disease_events_90d: int
    expected_births_60d: int
