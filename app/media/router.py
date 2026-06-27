from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, DbSession, Pagination, TenantId, require_perm
from app.media.schemas import AttachmentOut
from app.media.service import MediaService
from app.shared.schemas import Message, Page

router = APIRouter(prefix="/media", tags=["media"])


@router.post("", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_perm("media:create"))])
async def upload(
    session: DbSession,
    tenant_id: TenantId,
    user: CurrentUser,
    file: UploadFile = File(...),
    ref_type: str | None = Form(None),
    ref_id: str | None = Form(None),
    caption: str | None = Form(None),
):
    """Upload a picture/file and optionally attach it to any record (ref_type/ref_id)."""
    data = await file.read()
    return await MediaService(session, tenant_id).save(
        data=data, filename=file.filename, content_type=file.content_type,
        ref_type=ref_type, ref_id=ref_id, caption=caption, uploaded_by=user.id,
    )


@router.get("", response_model=Page[AttachmentOut], dependencies=[Depends(require_perm("media:read"))])
async def list_media(
    session: DbSession,
    tenant_id: TenantId,
    pagination: Pagination,
    ref_type: str | None = Query(None),
    ref_id: str | None = Query(None),
):
    items, total = await MediaService(session, tenant_id).list(
        ref_type=ref_type, ref_id=ref_id, offset=pagination.offset, limit=pagination.limit
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/{attachment_id}/file", dependencies=[Depends(require_perm("media:read"))])
async def get_file(attachment_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    svc = MediaService(session, tenant_id)
    att = await svc.get(attachment_id)
    return FileResponse(svc.abs_path(att), media_type=att.content_type, filename=att.filename)


@router.delete("/{attachment_id}", response_model=Message, dependencies=[Depends(require_perm("media:delete"))])
async def delete_media(attachment_id: uuid.UUID, session: DbSession, tenant_id: TenantId):
    await MediaService(session, tenant_id).delete(attachment_id)
    return Message(message="Attachment deleted")
