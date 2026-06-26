"""training examples (AI learning data capture)

Revision ID: 0002_training_examples
Revises: 0001_initial
Create Date: 2026-06-16
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from app.datasets.models import TrainingExample

revision: str = "0002_training_examples"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    TrainingExample.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    TrainingExample.__table__.drop(bind=op.get_bind(), checkfirst=True)
