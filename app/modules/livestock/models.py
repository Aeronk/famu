from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TenantEntity
from app.database.types import GUID
from app.shared.enums import LivestockSpecies, LivestockStatus, Sex, enum_type


class Livestock(Base, TenantEntity):
    __tablename__ = "livestock"

    farm_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("farms.id", ondelete="CASCADE"), index=True
    )
    species: Mapped[LivestockSpecies] = mapped_column(enum_type(LivestockSpecies), nullable=False)
    tag_number: Mapped[str | None] = mapped_column(String(60), index=True, nullable=True)
    breed: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sex: Mapped[Sex | None] = mapped_column(enum_type(Sex), nullable=True)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[LivestockStatus] = mapped_column(
        enum_type(LivestockStatus), default=LivestockStatus.ACTIVE, nullable=False
    )
    acquired_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Vaccination(Base, TenantEntity):
    __tablename__ = "vaccinations"

    # Nullable for batch vaccinations (e.g. "vaccinated 20 cattle").
    livestock_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("livestock.id", ondelete="CASCADE"), index=True, nullable=True
    )
    head_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    vaccine: Mapped[str | None] = mapped_column(String(160), nullable=True)
    vaccination_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    dose: Mapped[str | None] = mapped_column(String(80), nullable=True)
    administered_by: Mapped[str | None] = mapped_column(String(160), nullable=True)
    next_due_date: Mapped[date | None] = mapped_column(Date, index=True, nullable=True)


class DiseaseEvent(Base, TenantEntity):
    __tablename__ = "disease_events"

    livestock_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("livestock.id", ondelete="CASCADE"), index=True, nullable=True
    )
    head_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    disease: Mapped[str] = mapped_column(String(160), nullable=False)
    diagnosed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    treatment: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(80), nullable=True)


class WeightRecord(Base, TenantEntity):
    __tablename__ = "weight_records"

    livestock_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("livestock.id", ondelete="CASCADE"), index=True
    )
    recorded_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)


class BreedingRecord(Base, TenantEntity):
    __tablename__ = "breeding_records"

    dam_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("livestock.id", ondelete="CASCADE"), index=True
    )
    sire_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("livestock.id", ondelete="SET NULL"), nullable=True
    )
    service_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_birth_date: Mapped[date | None] = mapped_column(Date, index=True, nullable=True)
    actual_birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    offspring_count: Mapped[int | None] = mapped_column(Integer, nullable=True)


class FeedRecord(Base, TenantEntity):
    __tablename__ = "feed_records"

    livestock_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("livestock.id", ondelete="CASCADE"), nullable=True
    )
    farm_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("farms.id", ondelete="CASCADE"), nullable=True
    )
    feed_type: Mapped[str] = mapped_column(String(120), nullable=False)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    cost: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    feed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
