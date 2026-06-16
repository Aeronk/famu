"""LLM + embeddings wrapper with a deterministic mock fallback.

When ``OPENAI_API_KEY`` is set we call OpenAI; otherwise we return deterministic
mock output so chat, embeddings and the whole AI stack work offline. The mock
embedding is a hashed bag-of-words vector, so semantically similar text still
produces similar vectors — good enough for RAG demos.
"""

from __future__ import annotations

import hashlib
import math
import re

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMClient:
    def __init__(self) -> None:
        self.enabled = settings.openai_enabled
        self._client = None
        if self.enabled:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as exc:  # noqa: BLE001
                logger.warning("openai_init_failed", error=str(exc))
                self.enabled = False

    # ------------------------------------------------------------------ #
    # Chat
    # ------------------------------------------------------------------ #
    async def chat(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 600,
    ) -> str:
        if not self.enabled or self._client is None:
            return self._mock_chat(system, user)
        try:
            resp = await self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001
            logger.warning("openai_chat_failed", error=str(exc))
            return self._mock_chat(system, user)

    @staticmethod
    def _mock_chat(system: str, user: str) -> str:
        return (
            "[mock-advisor] Based on good agronomic practice: "
            f"{user.strip()[:160]} — ensure correct spacing, timely fertilizer "
            "application, integrated pest management, and soil-moisture monitoring. "
            "Configure OPENAI_API_KEY for full AI responses."
        )

    # ------------------------------------------------------------------ #
    # Embeddings
    # ------------------------------------------------------------------ #
    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.enabled or self._client is None:
            return [self._mock_embed(t) for t in texts]
        try:
            resp = await self._client.embeddings.create(
                model=settings.OPENAI_EMBED_MODEL, input=texts
            )
            return [d.embedding for d in resp.data]
        except Exception as exc:  # noqa: BLE001
            logger.warning("openai_embed_failed", error=str(exc))
            return [self._mock_embed(t) for t in texts]

    @staticmethod
    def _mock_embed(text: str) -> list[float]:
        dim = settings.EMBED_DIM
        vec = [0.0] * dim
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            h = int(hashlib.md5(token.encode()).hexdigest(), 16)
            vec[h % dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


llm = LLMClient()
