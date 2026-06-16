from __future__ import annotations

from abc import ABC, abstractmethod

from app.shared.enums import NotificationChannel


class Channel(ABC):
    name: NotificationChannel

    @abstractmethod
    async def send(self, *, to: str, body: str, title: str | None = None) -> tuple[bool, str | None]:
        """Return ``(success, error)``."""
        raise NotImplementedError


def get_channel(channel: NotificationChannel) -> Channel:
    from app.notifications.channels.email import EmailChannel
    from app.notifications.channels.sms import SmsChannel
    from app.notifications.channels.whatsapp import WhatsAppChannel

    return {
        NotificationChannel.WHATSAPP: WhatsAppChannel(),
        NotificationChannel.SMS: SmsChannel(),
        NotificationChannel.EMAIL: EmailChannel(),
    }[channel]
