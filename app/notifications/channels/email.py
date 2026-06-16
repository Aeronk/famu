from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.core.logging import get_logger
from app.notifications.channels.base import Channel
from app.shared.enums import NotificationChannel

logger = get_logger(__name__)


class EmailChannel(Channel):
    name = NotificationChannel.EMAIL

    async def send(self, *, to: str, body: str, title: str | None = None) -> tuple[bool, str | None]:
        if not settings.email_enabled:
            logger.info("email_stub", to=to, subject=title, body=body)
            return True, None
        try:
            msg = EmailMessage()
            msg["From"] = settings.EMAIL_FROM
            msg["To"] = to
            msg["Subject"] = title or "Murimi OS notification"
            msg.set_content(body)
            with smtplib.SMTP(settings.EMAIL_SMTP_HOST, settings.EMAIL_SMTP_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_SMTP_USER, settings.EMAIL_SMTP_PASSWORD)
                server.send_message(msg)
            return True, None
        except Exception as exc:  # noqa: BLE001
            logger.warning("email_send_failed", error=str(exc))
            return False, str(exc)
