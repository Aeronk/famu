from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.shared.enums import (
    Language,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from app.shared.schemas import ORMModel


class NotificationOut(ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    channel: NotificationChannel
    type: NotificationType
    title: str | None
    body: str
    status: NotificationStatus
    scheduled_for: datetime | None
    sent_at: datetime | None
    created_at: datetime


class PreferenceUpdate(BaseModel):
    channels: list[NotificationChannel] | None = None
    language: Language | None = None


class PreferenceOut(ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID
    channels: list[str]
    language: Language
