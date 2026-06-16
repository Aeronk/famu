from __future__ import annotations

from app.modules.crops.models import Activity, CropCycle, CropInput, Harvest
from app.tenancy.repository import TenantRepository


class CropCycleRepo(TenantRepository[CropCycle]):
    model = CropCycle


class CropInputRepo(TenantRepository[CropInput]):
    model = CropInput


class HarvestRepo(TenantRepository[Harvest]):
    model = Harvest


class ActivityRepo(TenantRepository[Activity]):
    model = Activity
