"""Reusable model mixins: UUID PK, timestamps, and tenant scoping."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.database.types import GUID


class PkMixin:
    """UUID primary key (distributed-friendly, no central sequence)."""

    @declared_attr.directive
    def id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(GUID(), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    @declared_attr.directive
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @declared_attr.directive
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )


class TenantMixin:
    """Adds an indexed, NOT NULL ``tenant_id`` FK — the spine of multi-tenancy.

    Every business object inherits this so row-level filtering can be enforced
    uniformly by ``TenantRepository``.
    """

    @declared_attr
    def tenant_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(
            GUID(),
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )


class Entity(PkMixin, TimestampMixin):
    """Convenience base for non-tenant entities (id + timestamps)."""


class TenantEntity(PkMixin, TenantMixin, TimestampMixin):
    """Convenience base for tenant-scoped business entities."""
