from __future__ import annotations

from app.notifications.channels.base import Channel
from app.shared.enums import NotificationChannel


class WhatsAppChannel(Channel):
    name = NotificationChannel.WHATSAPP

    async def send(self, *, to: str, body: str, title: str | None = None) -> tuple[bool, str | None]:
        from app.whatsapp.client import send_text  # lazy import avoids cycles

        return await send_text(to=to, body=body)
