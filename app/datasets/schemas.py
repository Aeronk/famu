from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.shared.enums import Channel, DatasetStatus
from app.shared.schemas import ORMModel


class TrainingExampleCreate(BaseModel):
    dataset: str = Field(min_length=2, max_length=40)
    features: dict
    label: dict = Field(default_factory=dict)
    channel: Channel = Channel.WEB
    source: str = "manual"
    ref_type: str | None = None
    ref_id: str | None = None
    notes: str | None = None


class TrainingExampleUpdate(BaseModel):
    """Human-in-the-loop correction: verify / reject and optionally fix the label."""

    status: DatasetStatus | None = None
    label: dict | None = None
    notes: str | None = None


class TrainingExampleOut(ORMModel):
    id: uuid.UUID
    dataset: str
    channel: str
    source: str
    features: dict
    label: dict
    status: DatasetStatus
    ref_type: str | None
    ref_id: str | None
    notes: str | None
    created_at: datetime


class DatasetStat(BaseModel):
    dataset: str
    total: int
    verified: int
    unverified: int
    rejected: int


class DatasetStats(BaseModel):
    datasets: list[DatasetStat]
    total_examples: int
