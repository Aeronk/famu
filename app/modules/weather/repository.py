from __future__ import annotations

from app.modules.weather.models import WeatherAlert, WeatherRecord
from app.tenancy.repository import TenantRepository


class WeatherRecordRepo(TenantRepository[WeatherRecord]):
    model = WeatherRecord


class WeatherAlertRepo(TenantRepository[WeatherAlert]):
    model = WeatherAlert
