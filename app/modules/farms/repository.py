from __future__ import annotations

from app.modules.farms.models import Farm
from app.tenancy.repository import TenantRepository


class FarmRepo(TenantRepository[Farm]):
    model = Farm
