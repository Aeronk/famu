from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TenantEntity
from app.database.types import GUID, JSONB
from app.shared.enums import ImageAnalysisType, Language, MessageRole, enum_type


class AIConversation(Base, TenantEntity):
    __tablename__ = "ai_conversations"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    channel: Mapped[str] = mapped_column(String(40), default="whatsapp", nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AIMessage(Base, TenantEntity):
    __tablename__ = "ai_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ai_conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[MessageRole] = mapped_column(enum_type(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[Language] = mapped_column(enum_type(Language), default=Language.EN, nullable=False)
    intent: Mapped[str | None] = mapped_column(String(60), nullable=True)
    entities: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class ImageAnalysis(Base, TenantEntity):
    __tablename__ = "image_analyses"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    image_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    analysis_type: Mapped[ImageAnalysisType] = mapped_column(
        enum_type(ImageAnalysisType), default=ImageAnalysisType.AUTO, nullable=False
    )
    result: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
