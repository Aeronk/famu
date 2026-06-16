from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, Pagination, TenantId, require_perm
from app.notifications.schemas import NotificationOut
from app.notifications.service import NotificationService
from app.shared.schemas import Page

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=Page[NotificationOut], dependencies=[Depends(require_perm("notification:read"))])
async def list_notifications(session: DbSession, tenant_id: TenantId, pagination: Pagination):
    items, total = await NotificationService(session, tenant_id).list(
        offset=pagination.offset, limit=pagination.limit
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)
