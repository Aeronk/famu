from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.shared.enums import Channel, ImageAnalysisType, Language
from app.shared.schemas import ORMModel


class AskRequest(BaseModel):
    question: str = Field(min_length=2)
    language: Language | None = None


class Source(BaseModel):
    source: str
    title: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    language: str


class ChatRequest(BaseModel):
    text: str = Field(min_length=1)
    channel: Channel = Channel.WEB  # web | mobile | api — feeds NLU training data


class ChatResponse(BaseModel):
    reply: str
    intent: str
    entities: dict
    language: Language
    record_id: str | None
    follow_up: bool


class ImageAnalyzeRequest(BaseModel):
    image_url: str | None = None
    image_b64: str | None = None
    analysis_type: ImageAnalysisType = ImageAnalysisType.AUTO


class ImageAnalysisOut(ORMModel):
    id: uuid.UUID
    analysis_type: ImageAnalysisType
    result: dict
    confidence: float | None
    image_ref: str | None
