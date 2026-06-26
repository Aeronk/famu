from __future__ import annotations

from app.datasets.models import TrainingExample
from app.tenancy.repository import TenantRepository


class TrainingExampleRepo(TenantRepository[TrainingExample]):
    model = TrainingExample
