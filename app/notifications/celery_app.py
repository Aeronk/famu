"""Celery application + beat schedule for background jobs.

Run a worker:   celery -A app.notifications.celery_app worker --loglevel=info -P solo
Run the beat:   celery -A app.notifications.celery_app beat --loglevel=info
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "murimi",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Africa/Harare",
    enable_utc=True,
    task_track_started=True,
)

# Import task module so tasks register with this app.
celery_app.autodiscover_tasks(["app.notifications"])
import app.notifications.tasks  # noqa: E402,F401

celery_app.conf.beat_schedule = {
    "vaccination-reminders-daily": {
        "task": "notifications.vaccination_reminders",
        "schedule": crontab(hour=6, minute=0),
    },
    "irrigation-reminders-daily": {
        "task": "notifications.irrigation_reminders",
        "schedule": crontab(hour=5, minute=30),
    },
    "weather-sync-twice-daily": {
        "task": "notifications.sync_weather",
        "schedule": crontab(hour="6,18", minute=0),
    },
    "disease-risk-scan-daily": {
        "task": "notifications.disease_risk_scan",
        "schedule": crontab(hour=7, minute=0),
    },
}
