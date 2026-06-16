"""Backend-portable column types.

The platform targets PostgreSQL + pgvector in production, but also runs on SQLite
for zero-dependency local development. These types pick the right native
representation per dialect:

* ``GUID``        -> native UUID on PG, CHAR(36) (dashed) elsewhere
* ``JSONB``       -> JSONB on PG, JSON elsewhere
* ``embedding_col`` -> pgvector ``vector(n)`` on PG, JSON list elsewhere
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB as _PG_JSONB
from sqlalchemy.dialects.postgresql import UUID as _PG_UUID
from sqlalchemy.types import CHAR, TypeDecorator


class GUID(TypeDecorator):
    """Platform-independent UUID stored dashed so string comparisons match."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(_PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(str(value))
        return value if dialect.name == "postgresql" else str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


# JSONB on Postgres, generic JSON (text) on SQLite — reusable shared instance.
JSONB = sa.JSON().with_variant(_PG_JSONB(), "postgresql")


def embedding_col(dim: int):
    """Vector column: pgvector on PG, JSON list elsewhere."""
    return sa.JSON().with_variant(Vector(dim), "postgresql")
