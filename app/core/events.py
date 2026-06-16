"""Lightweight in-process event bus (Event-Driven Architecture seam).

Domain services publish events; subscribers react (notifications, analytics,
audit, etc.). The interface is queue-agnostic — swap the in-process bus for an
outbox + broker later without touching publishers.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DomainEvent:
    name: str
    tenant_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


Handler = Callable[[DomainEvent], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: Handler) -> None:
        self._handlers[event_name].append(handler)

    def on(self, event_name: str) -> Callable[[Handler], Handler]:
        def decorator(handler: Handler) -> Handler:
            self.subscribe(event_name, handler)
            return handler

        return decorator

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(event.name, [])
        if not handlers:
            return
        results = await asyncio.gather(
            *(h(event) for h in handlers), return_exceptions=True
        )
        for result in results:
            if isinstance(result, Exception):
                logger.error("event_handler_failed", event=event.name, error=str(result))


event_bus = EventBus()
