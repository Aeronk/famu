from __future__ import annotations

import os
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.media.models import Attachment
from app.media.repository import AttachmentRepo
from app.shared.exceptions import NotFoundError, ValidationAppError

UPLOAD_ROOT = Path(settings.UPLOAD_DIR)


class MediaService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = AttachmentRepo(session, tenant_id)

    async def save(
        self,
        *,
        data: bytes,
        filename: str,
        content_type: str,
        ref_type: str | None,
        ref_id: str | None,
        caption: str | None,
        uploaded_by: uuid.UUID | None,
    ) -> Attachment:
        max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        if len(data) > max_bytes:
            raise ValidationAppError(f"File exceeds {settings.MAX_UPLOAD_MB} MB limit")
        if not data:
            raise ValidationAppError("Empty file")

        ext = os.path.splitext(filename or "")[1].lower() or ".bin"
        rel_path = f"{self.tenant_id}/{uuid.uuid4().hex}{ext}"
        dest = UPLOAD_ROOT / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

        kind = "image" if (content_type or "").startswith("image/") else "file"
        return await self.repo.create(
            ref_type=ref_type, ref_id=ref_id, kind=kind, filename=filename or "upload",
            content_type=content_type or "application/octet-stream", size_bytes=len(data),
            storage_path=rel_path, caption=caption, uploaded_by=uploaded_by,
        )

    async def list(self, *, ref_type: str | None, ref_id: str | None, offset: int, limit: int):
        filters: dict = {}
        if ref_type:
            filters["ref_type"] = ref_type
        if ref_id:
            filters["ref_id"] = ref_id
        return await self.repo.list(offset=offset, limit=limit, **filters), await self.repo.count(**filters)

    async def get(self, attachment_id: uuid.UUID) -> Attachment:
        return await self.repo.get_or_404(attachment_id)

    def abs_path(self, attachment: Attachment) -> Path:
        path = UPLOAD_ROOT / attachment.storage_path
        if not path.exists():
            raise NotFoundError("File data not found")
        return path

    async def delete(self, attachment_id: uuid.UUID) -> None:
        att = await self.repo.get_or_404(attachment_id)
        try:
            (UPLOAD_ROOT / att.storage_path).unlink(missing_ok=True)
        except OSError:
            pass
        await self.repo.delete(att)
