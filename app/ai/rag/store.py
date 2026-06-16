"""pgvector-backed retrieval store for the agricultural knowledge base."""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import llm
from app.ai.rag.models import KnowledgeChunk, KnowledgeDocument
from app.database.session import engine


@dataclass
class RetrievedChunk:
    content: str
    source: str
    title: str
    score: float


def chunk_text(text: str, *, size: int = 800, overlap: int = 120) -> list[str]:
    text = " ".join(text.split())
    if len(text) <= size:
        return [text] if text else []
    chunks, start = [], 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


class VectorStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_document(
        self,
        *,
        source: str,
        title: str,
        text: str,
        language: str = "en",
        tenant_id: uuid.UUID | None = None,
        meta: dict | None = None,
    ) -> KnowledgeDocument:
        doc = KnowledgeDocument(
            source=source, title=title, language=language, tenant_id=tenant_id, meta=meta or {}
        )
        self.session.add(doc)
        await self.session.flush()

        chunks = chunk_text(text)
        embeddings = await llm.embed(chunks) if chunks else []
        for i, (content, emb) in enumerate(zip(chunks, embeddings, strict=False)):
            self.session.add(
                KnowledgeChunk(
                    document_id=doc.id,
                    tenant_id=tenant_id,
                    ord=i,
                    content=content,
                    embedding=emb,
                    meta={"source": source, "title": title},
                )
            )
        await self.session.flush()
        return doc

    async def search(
        self, query: str, *, tenant_id: uuid.UUID | None = None, k: int = 4
    ) -> list[RetrievedChunk]:
        embedding = (await llm.embed([query]))[0]
        tenant_filter = or_(
            KnowledgeChunk.tenant_id.is_(None),
            KnowledgeChunk.tenant_id == (str(tenant_id) if tenant_id else None),
        )

        if engine.dialect.name == "postgresql":
            distance = KnowledgeChunk.embedding.cosine_distance(embedding)
            stmt = (
                select(
                    KnowledgeChunk.content,
                    KnowledgeDocument.source,
                    KnowledgeDocument.title,
                    distance.label("distance"),
                )
                .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
                .where(tenant_filter)
                .order_by(distance)
                .limit(k)
            )
            rows = (await self.session.execute(stmt)).all()
            return [
                RetrievedChunk(content=c, source=s, title=t, score=round(1 - float(d), 4))
                for c, s, t, d in rows
            ]

        # SQLite (and any non-pgvector backend): compute cosine similarity in Python.
        stmt = (
            select(
                KnowledgeChunk.content,
                KnowledgeDocument.source,
                KnowledgeDocument.title,
                KnowledgeChunk.embedding,
            )
            .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
            .where(tenant_filter)
        )
        rows = (await self.session.execute(stmt)).all()
        scored = [
            RetrievedChunk(content=c, source=s, title=t, score=_cosine(embedding, emb or []))
            for c, s, t, emb in rows
        ]
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:k]


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return round(dot / (na * nb), 4) if na and nb else 0.0
