"""Weather provider abstraction.

Returns live data from OpenWeather when ``WEATHER_API_KEY`` is set, otherwise a
deterministic synthetic reading so the platform works without credentials.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class WeatherReading:
    observed_at: datetime
    rainfall_mm: float
    temp_c: float
    humidity: float
    wind_kph: float
    source: str


def _synthetic(lat: float, lng: float) -> WeatherReading:
    """Deterministic pseudo-weather (seasonally plausible for Southern Africa)."""
    now = datetime.now(UTC)
    seed = (abs(lat) * 7 + abs(lng) * 13 + now.timetuple().tm_yday) % 100
    # Southern hemisphere: wet/warm Nov-Mar, dry/cooler May-Aug.
    month = now.month
    wet = month in (11, 12, 1, 2, 3)
    temp = 24 + 6 * math.sin(seed / 15) - (4 if not wet else 0)
    rain = (12 + seed % 25) if wet else max(0.0, seed % 6 - 3)
    return WeatherReading(
        observed_at=now,
        rainfall_mm=round(rain, 1),
        temp_c=round(temp, 1),
        humidity=round(55 + seed % 35, 1),
        wind_kph=round(6 + seed % 18, 1),
        source="synthetic",
    )


async def fetch_weather(lat: float | None, lng: float | None) -> WeatherReading:
    lat = lat if lat is not None else -17.83  # Harare default
    lng = lng if lng is not None else 31.05
    if not settings.weather_enabled:
        return _synthetic(lat, lng)

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lng, "appid": settings.WEATHER_API_KEY, "units": "metric"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        return WeatherReading(
            observed_at=datetime.now(UTC),
            rainfall_mm=float(data.get("rain", {}).get("1h", 0.0)),
            temp_c=float(data["main"]["temp"]),
            humidity=float(data["main"]["humidity"]),
            wind_kph=round(float(data["wind"]["speed"]) * 3.6, 1),
            source=settings.WEATHER_PROVIDER,
        )
    except Exception as exc:  # noqa: BLE001 — fall back rather than fail
        logger.warning("weather_provider_failed", error=str(exc))
        return _synthetic(lat, lng)
