from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.modules.auth.repository import UserRepo
from app.notifications.channels import get_channel
from app.notifications.models import Notification
from app.notifications.repository import NotificationRepo
from app.shared.enums import NotificationChannel, NotificationStatus, NotificationType

logger = get_logger(__name__)


class NotificationService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = NotificationRepo(session, tenant_id)
        self.users = UserRepo(session)

    async def _recipient_address(self, user_id: uuid.UUID, channel: NotificationChannel) -> str | None:
        user = await self.users.get(user_id)
        if not user:
            return None
        if channel == NotificationChannel.EMAIL:
            return user.email
        return user.phone_number  # whatsapp + sms

    async def dispatch(
        self,
        *,
        user_id: uuid.UUID | None,
        channel: NotificationChannel,
        body: str,
        title: str | None = None,
        type: NotificationType = NotificationType.GENERAL,
        payload: dict | None = None,
    ) -> Notification:
        notification = await self.repo.create(
            user_id=user_id,
            channel=channel,
            type=type,
            title=title,
            body=body,
            payload=payload or {},
            status=NotificationStatus.PENDING,
        )

        address = await self._recipient_address(user_id, channel) if user_id else None
        if not address:
            notification.status = NotificationStatus.FAILED
            notification.error = "No recipient address for channel"
            return notification

        ok, error = await get_channel(channel).send(to=address, body=body, title=title)
        notification.status = NotificationStatus.SENT if ok else NotificationStatus.FAILED
        notification.sent_at = datetime.now(UTC) if ok else None
        notification.error = error
        return notification

    async def list(self, *, offset: int, limit: int):
        return await self.repo.list(offset=offset, limit=limit), await self.repo.count()
