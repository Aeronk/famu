from __future__ import annotations

from pydantic import BaseModel, Field

from app.shared.enums import CropType


class YieldPredictRequest(BaseModel):
    crop: CropType
    area: float = Field(gt=0)
    variety: str | None = None
    rainfall_mm: float | None = None
    fertilizer_factor: float | None = Field(default=None, ge=0, le=1.5)
    history_factor: float | None = Field(default=None, ge=0, le=1.5)
    target_ref: str | None = None


class DiseasePredictRequest(BaseModel):
    crop: CropType
    humidity: float = Field(default=60, ge=0, le=100)
    rainfall_mm: float = Field(default=5, ge=0)
    temp_c: float = Field(default=24, ge=-10, le=55)
    target_ref: str | None = None


class RevenuePredictRequest(BaseModel):
    crop: CropType
    expected_yield: float = Field(ge=0)
    price_per_tonne: float | None = Field(default=None, ge=0)
    costs: float = Field(default=0, ge=0)
    target_ref: str | None = None


class PredictionResponse(BaseModel):
    type: str
    output: dict
    model_version: str
    confidence: float | None
