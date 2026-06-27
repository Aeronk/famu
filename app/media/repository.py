from __future__ import annotations

from app.media.models import Attachment
from app.tenancy.repository import TenantRepository


class AttachmentRepo(TenantRepository[Attachment]):
    model = Attachment
