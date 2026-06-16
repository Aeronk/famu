from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.shared.enums import AlertSeverity
from app.shared.schemas import ORMModel


class WeatherSyncRequest(BaseModel):
    farm_id: uuid.UUID | None = None
    lat: float | None = None
    lng: float | None = None


class WeatherRecordOut(ORMModel):
    id: uuid.UUID
    farm_id: uuid.UUID | None
    lat: float | None
    lng: float | None
    observed_at: datetime
    rainfall_mm: float | None
    temp_c: float | None
    humidity: float | None
    wind_kph: float | None
    source: str


class WeatherAlertOut(ORMModel):
    id: uuid.UUID
    farm_id: uuid.UUID | None
    type: str
    severity: AlertSeverity
    message: str
    valid_from: datetime | None
    valid_to: datetime | None
    created_at: datetime
