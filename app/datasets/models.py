from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TenantEntity
from app.database.types import GUID, JSONB
from app.shared.enums import DatasetStatus, enum_type


class TrainingExample(Base, TenantEntity):
    """A labeled example captured for AI/ML learning.

    Captured uniformly from every channel (web / mobile / WhatsApp / API), so the
    same structured dataset feeds model training regardless of how the farmer
    interacted. Human review promotes ``unverified`` -> ``verified`` (gold labels).
    """

    __tablename__ = "training_examples"

    dataset: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(20), default="api", nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="auto", nullable=False)  # auto|manual|correction
    features: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    label: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[DatasetStatus] = mapped_column(
        enum_type(DatasetStatus), default=DatasetStatus.UNVERIFIED, nullable=False, index=True
    )
    # Link back to the source record so auto-capture can dedupe / update.
    ref_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ref_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
