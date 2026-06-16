from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TenantEntity
from app.database.types import GUID


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

    # Agronomy
    soil_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    water_source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    irrigation_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    size_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
