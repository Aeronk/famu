"""farm profile fields + national-sharing tracking

Revision ID: 0003_farm_profile_and_sharing
Revises: 0002_training_examples
Create Date: 2026-06-16
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_farm_profile_and_sharing"
down_revision: str | None = "0002_training_examples"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("farms") as b:
        b.add_column(sa.Column("farming_type", sa.String(40), nullable=False, server_default="personal"))
        b.add_column(sa.Column("enterprise_type", sa.String(40), nullable=False, server_default="mixed"))
    with op.batch_alter_table("training_examples") as b:
        b.add_column(sa.Column("shared_national", sa.Boolean(), nullable=False, server_default=sa.false()))
        b.add_column(sa.Column("shared_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("training_examples") as b:
        b.drop_column("shared_at")
        b.drop_column("shared_national")
    with op.batch_alter_table("farms") as b:
        b.drop_column("enterprise_type")
        b.drop_column("farming_type")
