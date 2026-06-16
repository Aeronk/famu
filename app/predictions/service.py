from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.predictions.disease_model import DiseaseModel
from app.predictions.models import Prediction
from app.predictions.repository import PredictionRepo
from app.predictions.revenue_model import RevenueModel
from app.predictions.yield_model import YieldModel
from app.shared.enums import PredictionType


class PredictionService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.tenant_id = tenant_id
        self.repo = PredictionRepo(session, tenant_id)
        self.yield_model = YieldModel()
        self.disease_model = DiseaseModel()
        self.revenue_model = RevenueModel()

    async def _store(self, type_: PredictionType, model, features: dict, target_ref: str | None) -> Prediction:
        output = model.predict(features)
        return await self.repo.create(
            type=type_,
            target_ref=target_ref,
            inputs=features,
            output=output,
            model_version=model.version,
            confidence=output.get("confidence"),
        )

    async def predict_yield(self, features: dict, *, target_ref: str | None = None) -> Prediction:
        return await self._store(PredictionType.YIELD, self.yield_model, features, target_ref)

    async def predict_disease(self, features: dict, *, target_ref: str | None = None) -> Prediction:
        return await self._store(PredictionType.DISEASE, self.disease_model, features, target_ref)

    async def predict_revenue(self, features: dict, *, target_ref: str | None = None) -> Prediction:
        return await self._store(PredictionType.REVENUE, self.revenue_model, features, target_ref)
