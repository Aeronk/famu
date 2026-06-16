from __future__ import annotations

from app.predictions.models import Prediction
from app.tenancy.repository import TenantRepository


class PredictionRepo(TenantRepository[Prediction]):
    model = Prediction
