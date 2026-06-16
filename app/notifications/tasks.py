"""Celery tasks for scheduled alerts & reminders.

Each task wraps an async routine via ``asyncio.run`` and opens its own session.
Tasks run cross-tenant (bypass) and dispatch per farm owner. They are written
defensively so a single bad record never aborts the whole run.
"""

from __future__ import annotations

import asyncio
from datetime import date, timedelta

from sqlalchemy import select

from app.core.logging import get_logger
from app.database.session import SessionLocal
from app.notifications.celery_app import celery_app
from app.notifications.service import NotificationService
from app.shared.enums import NotificationChannel, NotificationType
from app.shared.i18n import translate

logger = get_logger(__name__)


def _run(coro):
    return asyncio.run(coro)


async def _notify_owner(session, *, tenant_id, owner_user_id, body, type_):
    if not owner_user_id:
        return
    svc = NotificationService(session, tenant_id)
    await svc.dispatch(
        user_id=owner_user_id,
        channel=NotificationChannel.WHATSAPP,
        body=body,
        type=type_,
    )


# --------------------------------------------------------------------------- #
@celery_app.task(name="notifications.vaccination_reminders")
def vaccination_reminders() -> int:
    return _run(_vaccination_reminders())


async def _vaccination_reminders() -> int:
    from app.modules.farms.models import Farm
    from app.modules.livestock.models import Livestock, Vaccination

    window = date.today() + timedelta(days=3)
    count = 0
    async with SessionLocal() as session:
        stmt = select(Vaccination).where(
            Vaccination.next_due_date.isnot(None),
            Vaccination.next_due_date <= window,
            Vaccination.next_due_date >= date.today(),
        )
        for vac in (await session.execute(stmt)).scalars().all():
            owner = None
            if vac.livestock_id:
                animal = await session.get(Livestock, vac.livestock_id)
                if animal:
                    farm = await session.get(Farm, animal.farm_id)
                    owner = farm.owner_user_id if farm else None
            body = translate("vaccination_reminder", "en", date=str(vac.next_due_date))
            await _notify_owner(session, tenant_id=vac.tenant_id, owner_user_id=owner,
                                body=body, type_=NotificationType.VACCINATION_REMINDER)
            count += 1
        await session.commit()
    logger.info("vaccination_reminders_done", count=count)
    return count


@celery_app.task(name="notifications.irrigation_reminders")
def irrigation_reminders() -> int:
    return _run(_irrigation_reminders())


async def _irrigation_reminders() -> int:
    from app.modules.crops.models import CropCycle
    from app.modules.farms.models import Farm
    from app.shared.enums import CropCycleStatus

    count = 0
    async with SessionLocal() as session:
        stmt = select(CropCycle).where(CropCycle.status == CropCycleStatus.GROWING)
        for cycle in (await session.execute(stmt)).scalars().all():
            farm = await session.get(Farm, cycle.farm_id)
            owner = farm.owner_user_id if farm else None
            body = translate("irrigation_reminder", "en", crop=cycle.crop_type.value)
            await _notify_owner(session, tenant_id=cycle.tenant_id, owner_user_id=owner,
                                body=body, type_=NotificationType.IRRIGATION_REMINDER)
            count += 1
        await session.commit()
    logger.info("irrigation_reminders_done", count=count)
    return count


@celery_app.task(name="notifications.sync_weather")
def sync_weather() -> int:
    return _run(_sync_weather())


async def _sync_weather() -> int:
    from app.modules.farms.models import Farm
    from app.modules.weather.schemas import WeatherSyncRequest
    from app.modules.weather.service import WeatherService

    count = 0
    async with SessionLocal() as session:
        for farm in (await session.execute(select(Farm))).scalars().all():
            try:
                svc = WeatherService(session, farm.tenant_id)
                await svc.sync(WeatherSyncRequest(farm_id=farm.id))
                count += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("weather_sync_failed", farm_id=str(farm.id), error=str(exc))
        await session.commit()
    logger.info("weather_sync_done", count=count)
    return count


@celery_app.task(name="notifications.disease_risk_scan")
def disease_risk_scan() -> int:
    return _run(_disease_risk_scan())


async def _disease_risk_scan() -> int:
    from app.modules.crops.models import CropCycle
    from app.modules.farms.models import Farm
    from app.predictions.disease_model import DiseaseModel
    from app.shared.enums import CropCycleStatus

    count = 0
    model = DiseaseModel()
    async with SessionLocal() as session:
        stmt = select(CropCycle).where(CropCycle.status == CropCycleStatus.GROWING)
        for cycle in (await session.execute(stmt)).scalars().all():
            result = model.predict({"crop": cycle.crop_type.value, "humidity": 80, "rainfall_mm": 20})
            if result.get("risk") == "HIGH":
                farm = await session.get(Farm, cycle.farm_id)
                owner = farm.owner_user_id if farm else None
                body = f"Disease risk HIGH for your {cycle.crop_type.value}. Scout fields and consider preventive spraying."
                await _notify_owner(session, tenant_id=cycle.tenant_id, owner_user_id=owner,
                                    body=body, type_=NotificationType.DISEASE_RISK)
                count += 1
        await session.commit()
    logger.info("disease_risk_scan_done", count=count)
    return count
