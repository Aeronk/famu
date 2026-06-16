from __future__ import annotations

from pydantic import BaseModel, Field

from app.shared.enums import CropType


class ScenarioChange(BaseModel):
    """Deltas applied to the baseline. e.g. 'plant tomatoes', 'rainfall -20%'."""

    new_crop: CropType | None = None
    area: float | None = Field(default=None, gt=0)
    rainfall_delta_pct: float = Field(default=0, ge=-100, le=200)
    price_delta_pct: float = Field(default=0, ge=-100, le=500)
    fertilizer_factor: float | None = Field(default=None, ge=0, le=1.5)
    costs: float | None = Field(default=None, ge=0)


class SimulationRequest(BaseModel):
    crop: CropType
    area: float = Field(gt=0)
    rainfall_mm: float = Field(default=550, ge=0)
    fertilizer_factor: float = Field(default=0.85, ge=0, le=1.5)
    price_per_tonne: float | None = Field(default=None, ge=0)
    costs: float = Field(default=0, ge=0)
    scenario: ScenarioChange


class Outcome(BaseModel):
    crop: str
    area_ha: float
    expected_yield: float
    revenue: float
    costs: float
    profit: float


class SimulationResult(BaseModel):
    baseline: Outcome
    scenario: Outcome
    deltas: dict
