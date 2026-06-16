from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.notifications.channels.base import Channel
from app.shared.enums import NotificationChannel

logger = get_logger(__name__)


class SmsChannel(Channel):
    name = NotificationChannel.SMS

    async def send(self, *, to: str, body: str, title: str | None = None) -> tuple[bool, str | None]:
        if not settings.sms_enabled:
            logger.info("sms_stub", to=to, body=body)
            return True, None
        # Generic HTTP SMS gateway example (provider-specific wiring goes here).
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://api.sms-provider.example/send",
                    json={"to": to, "from": settings.SMS_SENDER_ID, "text": body},
                    headers={"Authorization": f"Bearer {settings.SMS_API_KEY}"},
                )
                resp.raise_for_status()
            return True, None
        except Exception as exc:  # noqa: BLE001
            logger.warning("sms_send_failed", error=str(exc))
            return False, str(exc)
