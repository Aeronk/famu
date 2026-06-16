"""initial schema

Creates the pgvector extension, all tables (from the SQLAlchemy metadata, the
single source of truth), and — when ENABLE_RLS is set — optional Postgres
row-level security policies keyed on the ``app.current_tenant`` GUC.

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-15
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from app.core.config import settings
from app.database.models import Base

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Tenant-scoped tables (NOT NULL tenant_id) eligible for RLS.
RLS_TABLES = [
    "farms", "crop_cycles", "crop_inputs", "harvests", "activities",
    "tobacco_cycles", "tobacco_reaping", "tobacco_curing", "tobacco_grading", "tobacco_deliveries",
    "livestock", "vaccinations", "disease_events", "weight_records", "breeding_records", "feed_records",
    "expenses", "incomes", "loans", "input_credits",
    "weather_records", "weather_alerts",
    "ai_conversations", "ai_messages", "image_analyses",
    "predictions", "simulations",
    "notifications", "notification_preferences",
    "whatsapp_contacts",
]


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"
    if is_pg:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    Base.metadata.create_all(bind=bind)

    if settings.ENABLE_RLS and is_pg:
        for table in RLS_TABLES:
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
            op.execute(
                f"""
                CREATE POLICY {table}_tenant_isolation ON {table}
                USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid)
                """
            )


def downgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"
    if settings.ENABLE_RLS and is_pg:
        for table in RLS_TABLES:
            op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
            op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    Base.metadata.drop_all(bind=bind)
    if is_pg:
        op.execute("DROP EXTENSION IF EXISTS vector")
