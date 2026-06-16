from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, TenantId, require_perm
from app.predictions.schemas import (
    DiseasePredictRequest,
    PredictionResponse,
    RevenuePredictRequest,
    YieldPredictRequest,
)
from app.predictions.service import PredictionService

router = APIRouter(prefix="/predictions", tags=["predictions"])


def _to_response(prediction) -> PredictionResponse:
    return PredictionResponse(
        type=prediction.type.value,
        output=prediction.output,
        model_version=prediction.model_version,
        confidence=prediction.confidence,
    )


@router.post("/yield", response_model=PredictionResponse, dependencies=[Depends(require_perm("prediction:read"))])
async def predict_yield(payload: YieldPredictRequest, session: DbSession, tenant_id: TenantId):
    features = payload.model_dump(exclude={"target_ref"}, exclude_none=True)
    features["crop"] = payload.crop.value
    prediction = await PredictionService(session, tenant_id).predict_yield(
        features, target_ref=payload.target_ref
    )
    return _to_response(prediction)


@router.post("/disease", response_model=PredictionResponse, dependencies=[Depends(require_perm("prediction:read"))])
async def predict_disease(payload: DiseasePredictRequest, session: DbSession, tenant_id: TenantId):
    features = payload.model_dump(exclude={"target_ref"})
    features["crop"] = payload.crop.value
    prediction = await PredictionService(session, tenant_id).predict_disease(
        features, target_ref=payload.target_ref
    )
    return _to_response(prediction)


@router.post("/revenue", response_model=PredictionResponse, dependencies=[Depends(require_perm("prediction:read"))])
async def predict_revenue(payload: RevenuePredictRequest, session: DbSession, tenant_id: TenantId):
    features = payload.model_dump(exclude={"target_ref"})
    features["crop"] = payload.crop.value
    prediction = await PredictionService(session, tenant_id).predict_revenue(
        features, target_ref=payload.target_ref
    )
    return _to_response(prediction)
