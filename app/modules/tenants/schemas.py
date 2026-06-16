from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.shared.enums import TenantStatus, TenantType
from app.shared.schemas import ORMModel


class TenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9-]+$")
    type: TenantType = TenantType.SMALLHOLDER
    plan: str = "free"
    country: str | None = "Zimbabwe"
    settings: dict[str, Any] = Field(default_factory=dict)


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=160)
    type: TenantType | None = None
    status: TenantStatus | None = None
    plan: str | None = None
    country: str | None = None
    settings: dict[str, Any] | None = None


class TenantOut(ORMModel):
    id: uuid.UUID
    name: str
    slug: str
    type: TenantType
    status: TenantStatus
    plan: str
    country: str | None
    settings: dict[str, Any]
    created_at: datetime
