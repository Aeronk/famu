"""RAG-backed advisory agent: retrieve knowledge, then answer (grounded)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import llm
from app.ai.prompts import ADVISORY_SYSTEM, language_instruction
from app.ai.rag.store import VectorStore
from app.shared.enums import Language


class AdvisoryService:
    def __init__(self, session: AsyncSession):
        self.store = VectorStore(session)

    async def ask(
        self,
        question: str,
        *,
        tenant_id: uuid.UUID | None = None,
        language: Language = Language.EN,
    ) -> dict:
        chunks = await self.store.search(question, tenant_id=tenant_id, k=4)
        context = "\n\n".join(f"[{c.source}: {c.title}] {c.content}" for c in chunks)
        system = f"{ADVISORY_SYSTEM}\n{language_instruction(language)}"
        user = (
            f"Knowledge base context:\n{context}\n\n"
            f"Farmer's question: {question}\n\n"
            "Answer using the context where relevant."
        )
        answer = await llm.chat(system=system, user=user)
        return {
            "answer": answer,
            "sources": [
                {"source": c.source, "title": c.title, "score": c.score} for c in chunks
            ],
            "language": language.value,
        }
