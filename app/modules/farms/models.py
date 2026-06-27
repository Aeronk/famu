from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TenantEntity
from app.database.types import GUID
from app.shared.enums import EnterpriseType, FarmingType, enum_type


class Farm(Base, TenantEntity):
    __tablename__ = "farms"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Location
    gps_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    province: Mapped[str | None] = mapped_column(String(80), nullable=True)
    district: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ward: Mapped[str | None] = mapped_column(String(80), nullable=True)
    village: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Classification (strong signals for AI; commercial vs personal etc.)
    farming_type: Mapped[FarmingType] = mapped_column(
        enum_type(FarmingType), default=FarmingType.PERSONAL, nullable=False
    )
    enterprise_type: Mapped[EnterpriseType] = mapped_column(
        enum_type(EnterpriseType), default=EnterpriseType.MIXED, nullable=False
    )

    # Agronomy
    soil_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    water_source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    irrigation_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    size_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
