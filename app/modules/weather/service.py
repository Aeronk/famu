from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import DomainEvent, event_bus
from app.modules.farms.repository import FarmRepo
from app.modules.weather.models import WeatherAlert, WeatherRecord
from app.modules.weather.provider import WeatherReading, fetch_weather
from app.modules.weather.repository import WeatherAlertRepo, WeatherRecordRepo
from app.modules.weather.schemas import WeatherSyncRequest
from app.shared.enums import AlertSeverity


class WeatherService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.records = WeatherRecordRepo(session, tenant_id)
        self.alerts = WeatherAlertRepo(session, tenant_id)
        self.farms = FarmRepo(session, tenant_id)

    async def sync(self, req: WeatherSyncRequest) -> WeatherRecord:
        lat, lng = req.lat, req.lng
        if req.farm_id:
            farm = await self.farms.get_or_404(req.farm_id)
            lat = lat if lat is not None else farm.gps_lat
            lng = lng if lng is not None else farm.gps_lng

        reading = await fetch_weather(lat, lng)
        record = await self.records.create(
            farm_id=req.farm_id,
            lat=lat,
            lng=lng,
            observed_at=reading.observed_at,
            rainfall_mm=reading.rainfall_mm,
            temp_c=reading.temp_c,
            humidity=reading.humidity,
            wind_kph=reading.wind_kph,
            source=reading.source,
        )
        await self._generate_alerts(req.farm_id, reading)
        return record

    async def _generate_alerts(self, farm_id: uuid.UUID | None, reading: WeatherReading) -> list[WeatherAlert]:
        created: list[WeatherAlert] = []

        def add(type_: str, severity: AlertSeverity, message: str):
            return self.alerts.create(
                farm_id=farm_id,
                type=type_,
                severity=severity,
                message=message,
                valid_from=reading.observed_at,
            )

        if reading.rainfall_mm >= 25:
            created.append(await add("heavy_rain", AlertSeverity.HIGH,
                                     f"Heavy rainfall expected ({reading.rainfall_mm} mm). Check drainage."))
        if reading.temp_c >= 35:
            created.append(await add("heat_stress", AlertSeverity.MEDIUM,
                                     f"High temperatures ({reading.temp_c}°C). Irrigate and shade livestock."))
        if reading.temp_c <= 2:
            created.append(await add("frost", AlertSeverity.HIGH,
                                     f"Frost risk ({reading.temp_c}°C). Protect sensitive crops."))
        if reading.wind_kph >= 40:
            created.append(await add("strong_wind", AlertSeverity.MEDIUM,
                                     f"Strong winds ({reading.wind_kph} kph). Secure structures."))

        for alert in created:
            await event_bus.publish(
                DomainEvent(
                    name="weather.alert",
                    tenant_id=str(self.tenant_id),
                    payload={"type": alert.type, "severity": alert.severity.value, "farm_id": str(farm_id) if farm_id else None},
                )
            )
        return created

    async def list_records(self, *, offset: int, limit: int):
        return await self.records.list(offset=offset, limit=limit), await self.records.count()

    async def list_alerts(self, *, offset: int, limit: int):
        return await self.alerts.list(offset=offset, limit=limit), await self.alerts.count()
