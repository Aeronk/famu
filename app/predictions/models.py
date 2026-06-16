from __future__ import annotations

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TenantEntity
from app.database.types import JSONB
from app.shared.enums import PredictionType, enum_type


class Prediction(Base, TenantEntity):
    __tablename__ = "predictions"

    type: Mapped[PredictionType] = mapped_column(enum_type(PredictionType), nullable=False, index=True)
    target_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    inputs: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    output: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    model_version: Mapped[str] = mapped_column(String(40), default="heuristic-v1", nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
