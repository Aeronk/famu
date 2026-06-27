"""attachments (media / image uploads)

Revision ID: 0004_attachments
Revises: 0003_farm_profile_and_sharing
Create Date: 2026-06-16
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from app.media.models import Attachment

revision: str = "0004_attachments"
down_revision: str | None = "0003_farm_profile_and_sharing"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    Attachment.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    Attachment.__table__.drop(bind=op.get_bind(), checkfirst=True)
