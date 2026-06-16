from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TenantEntity
from app.database.types import GUID, JSONB


class WhatsAppContact(Base, TenantEntity):
    __tablename__ = "whatsapp_contacts"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    wa_phone: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    profile_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    opted_in: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Multi-turn conversation state, e.g. {"awaiting": "vaccine", "record_id": "..."}.
    state: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
