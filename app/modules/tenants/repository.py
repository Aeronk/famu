from __future__ import annotations

from app.modules.tenants.models import Tenant
from app.shared.repository import BaseRepository


class TenantRepo(BaseRepository[Tenant]):
    model = Tenant
