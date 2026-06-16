from __future__ import annotations

from app.modules.livestock.models import (
    BreedingRecord,
    DiseaseEvent,
    FeedRecord,
    Livestock,
    Vaccination,
    WeightRecord,
)
from app.tenancy.repository import TenantRepository


class LivestockRepo(TenantRepository[Livestock]):
    model = Livestock


class VaccinationRepo(TenantRepository[Vaccination]):
    model = Vaccination


class DiseaseEventRepo(TenantRepository[DiseaseEvent]):
    model = DiseaseEvent


class WeightRecordRepo(TenantRepository[WeightRecord]):
    model = WeightRecord


class BreedingRecordRepo(TenantRepository[BreedingRecord]):
    model = BreedingRecord


class FeedRecordRepo(TenantRepository[FeedRecord]):
    model = FeedRecord
