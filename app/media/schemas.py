from __future__ import annotations

import uuid
from datetime import datetime

from app.shared.schemas import ORMModel


class AttachmentOut(ORMModel):
    id: uuid.UUID
    ref_type: str | None
    ref_id: str | None
    kind: str
    filename: str
    content_type: str
    size_bytes: int
    caption: str | None
    created_at: datetime
