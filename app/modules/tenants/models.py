from __future__ import annotations

from typing import Any

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import Entity
from app.database.types import JSONB
from app.shared.enums import TenantStatus, TenantType, enum_type


class Tenant(Base, Entity):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    type: Mapped[TenantType] = mapped_column(
        enum_type(TenantType), default=TenantType.SMALLHOLDER, nullable=False
    )
    status: Mapped[TenantStatus] = mapped_column(
        enum_type(TenantStatus), default=TenantStatus.TRIAL, nullable=False
    )
    plan: Mapped[str] = mapped_column(String(40), default="free", nullable=False)
    country: Mapped[str | None] = mapped_column(String(80), default="Zimbabwe")
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
