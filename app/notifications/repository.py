from __future__ import annotations

from app.notifications.models import Notification, NotificationPreference
from app.tenancy.repository import TenantRepository


class NotificationRepo(TenantRepository[Notification]):
    model = Notification


class PreferenceRepo(TenantRepository[NotificationPreference]):
    model = NotificationPreference
