from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.shared.schemas import ORMModel


class MarketPriceCreate(BaseModel):
    commodity: str
    market: str | None = None
    price: float = Field(gt=0)
    currency: str = "USD"
    unit: str = "kg"
    price_date: date | None = None
    source: str | None = None


class MarketPriceUpdate(BaseModel):
    commodity: str | None = None
    market: str | None = None
    price: float | None = Field(default=None, gt=0)
    currency: str | None = None
    unit: str | None = None
    price_date: date | None = None
    source: str | None = None


class MarketPriceOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    commodity: str
    market: str | None
    price: float
    currency: str
    unit: str
    price_date: date | None
    source: str | None
    created_at: datetime


class LatestPrice(BaseModel):
    commodity: str
    price: float
    currency: str
    unit: str
    market: str | None
    price_date: date | None
