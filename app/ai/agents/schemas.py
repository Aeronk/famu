from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel

from app.shared.enums import Language


class ExtractionResult(BaseModel):
    intent: str = "unknown"
    entities: dict = {}
    confidence: float = 0.5


class AgentReply(BaseModel):
    reply: str
    intent: str
    entities: dict = {}
    language: Language = Language.EN
    record_id: str | None = None
    follow_up: bool = False


@dataclass
class AgentDeps:
    """Runtime dependencies injected into the agent graph (not serialized)."""

    session: object  # AsyncSession
    tenant_id: object  # uuid.UUID
    user_id: object | None = None  # uuid.UUID | None
    extra: dict = field(default_factory=dict)
