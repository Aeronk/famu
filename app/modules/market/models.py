from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import Entity
from app.database.types import GUID


class MarketPrice(Base, Entity):
    """Commodity reference prices. ``tenant_id`` NULL = global/shared price."""

    __tablename__ = "market_prices"

    # Nullable + no FK: NULL rows are global prices visible to every tenant.
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), nullable=True, index=True
    )
    commodity: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    market: Mapped[str | None] = mapped_column(String(120), nullable=True)
    price: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    unit: Mapped[str] = mapped_column(String(40), default="kg", nullable=False)
    price_date: Mapped[date | None] = mapped_column(Date, index=True, nullable=True)
    source: Mapped[str | None] = mapped_column(String(120), nullable=True)
