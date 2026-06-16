from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TenantEntity
from app.database.types import GUID


class TobaccoCycle(Base, TenantEntity):
    __tablename__ = "tobacco_cycles"

    farm_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("farms.id", ondelete="CASCADE"), index=True
    )
    variety: Mapped[str | None] = mapped_column(String(120), nullable=True)
    season: Mapped[str | None] = mapped_column(String(40), nullable=True)
    seedbed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    transplant_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    area_ha: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="growing", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class TobaccoReaping(Base, TenantEntity):
    __tablename__ = "tobacco_reaping"

    tobacco_cycle_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("tobacco_cycles.id", ondelete="CASCADE"), index=True
    )
    reap_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    mass_kg: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    bundles: Mapped[int | None] = mapped_column(Integer, nullable=True)


class TobaccoCuring(Base, TenantEntity):
    __tablename__ = "tobacco_curing"

    tobacco_cycle_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("tobacco_cycles.id", ondelete="CASCADE"), index=True
    )
    barn: Mapped[str | None] = mapped_column(String(80), nullable=True)
    method: Mapped[str | None] = mapped_column(String(40), nullable=True)  # flue / air / fire
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    mass_kg: Mapped[float] = mapped_column(Float, default=0, nullable=False)


class TobaccoGrading(Base, TenantEntity):
    __tablename__ = "tobacco_grading"

    tobacco_cycle_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("tobacco_cycles.id", ondelete="CASCADE"), index=True
    )
    grade: Mapped[str] = mapped_column(String(40), nullable=False)
    mass_kg: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    bales: Mapped[int | None] = mapped_column(Integer, nullable=True)


class TobaccoDelivery(Base, TenantEntity):
    __tablename__ = "tobacco_deliveries"

    tobacco_cycle_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("tobacco_cycles.id", ondelete="CASCADE"), index=True
    )
    floor: Mapped[str | None] = mapped_column(String(80), nullable=True)  # auction / contract floor
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    mass_kg: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    price_per_kg: Mapped[float] = mapped_column(Numeric(12, 4), default=0, nullable=False)
    gross_value: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    deductions: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    net_value: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
