from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TenantEntity
from app.database.types import GUID


class Attachment(Base, TenantEntity):
    """A stored file (usually a photo) attachable to any record.

    ``ref_type`` + ``ref_id`` form a generic, polymorphic link, so a picture can
    be attached to a farm, crop cycle, livestock animal, activity, etc.
    """

    __tablename__ = "attachments"

    ref_type: Mapped[str | None] = mapped_column(String(40), index=True, nullable=True)
    ref_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    kind: Mapped[str] = mapped_column(String(20), default="image", nullable=False)  # image | file
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), default="application/octet-stream", nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    caption: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
