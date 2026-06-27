"""Connector that feeds anonymized training data to a national AI service.

Posts in batches to ``NATIONAL_AI_ENDPOINT``. When unset, runs in mock mode
(logs and reports success) so the flow is testable without an external service.
"""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
_BATCH = 500


async def feed_national(dataset: str, rows: list[dict]) -> dict:
    if not rows:
        return {"dataset": dataset, "sent": 0, "status": "empty"}

    if not settings.national_ai_enabled:
        logger.info("national_ai_stub", dataset=dataset, count=len(rows))
        return {"dataset": dataset, "sent": len(rows), "status": "stub"}

    sent = 0
    headers = {"Authorization": f"Bearer {settings.NATIONAL_AI_API_KEY}"}
    async with httpx.AsyncClient(timeout=30) as client:
        for i in range(0, len(rows), _BATCH):
            batch = rows[i : i + _BATCH]
            resp = await client.post(
                settings.NATIONAL_AI_ENDPOINT,
                json={"dataset": dataset, "examples": batch},
                headers=headers,
            )
            resp.raise_for_status()
            sent += len(batch)
    return {"dataset": dataset, "sent": sent, "status": "delivered"}
