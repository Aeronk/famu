from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TenantEntity
from app.database.types import GUID, JSONB
from app.shared.enums import (
    Language,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
    enum_type,
)


class Notification(Base, TenantEntity):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    channel: Mapped[NotificationChannel] = mapped_column(enum_type(NotificationChannel), nullable=False)
    type: Mapped[NotificationType] = mapped_column(
        enum_type(NotificationType), default=NotificationType.GENERAL, nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(160), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        enum_type(NotificationStatus), default=NotificationStatus.PENDING, nullable=False, index=True
    )
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class NotificationPreference(Base, TenantEntity):
    __tablename__ = "notification_preferences"
    __table_args__ = (UniqueConstraint("user_id", name="uq_notification_preferences_user_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    channels: Mapped[list] = mapped_column(JSONB, default=lambda: ["whatsapp"], nullable=False)
    language: Mapped[Language] = mapped_column(
        enum_type(Language), default=Language.EN, nullable=False
    )
