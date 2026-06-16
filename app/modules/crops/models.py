from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TenantEntity
from app.database.types import GUID, JSONB
from app.shared.enums import (
    ActivitySource,
    CropCycleStatus,
    CropType,
    InputType,
    enum_type,
)


class CropCycle(Base, TenantEntity):
    __tablename__ = "crop_cycles"

    farm_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("farms.id", ondelete="CASCADE"), index=True, nullable=False
    )
    crop_type: Mapped[CropType] = mapped_column(enum_type(CropType), nullable=False)
    variety: Mapped[str | None] = mapped_column(String(120), nullable=True)
    season: Mapped[str | None] = mapped_column(String(40), nullable=True)
    planting_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    area_ha: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    status: Mapped[CropCycleStatus] = mapped_column(
        enum_type(CropCycleStatus), default=CropCycleStatus.PLANNED, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class CropInput(Base, TenantEntity):
    __tablename__ = "crop_inputs"

    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("crop_cycles.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[InputType] = mapped_column(enum_type(InputType), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    cost: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    applied_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class Harvest(Base, TenantEntity):
    __tablename__ = "harvests"

    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("crop_cycles.id", ondelete="CASCADE"), index=True
    )
    harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    quantity: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    unit: Mapped[str] = mapped_column(String(40), default="kg", nullable=False)
    quality_grade: Mapped[str | None] = mapped_column(String(40), nullable=True)
    revenue: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)


class Activity(Base, TenantEntity):
    """Cross-cutting activity log feeding crop & livestock timelines."""

    __tablename__ = "activities"

    farm_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("farms.id", ondelete="CASCADE"), index=True, nullable=True
    )
    crop_cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("crop_cycles.id", ondelete="CASCADE"), index=True, nullable=True
    )
    livestock_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("livestock.id", ondelete="CASCADE"), index=True, nullable=True
    )
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    activity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[ActivitySource] = mapped_column(
        enum_type(ActivitySource), default=ActivitySource.MANUAL, nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    meta: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
