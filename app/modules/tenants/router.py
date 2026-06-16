from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, DbSession, Pagination, require_role
from app.modules.tenants.schemas import TenantCreate, TenantOut, TenantUpdate
from app.modules.tenants.service import TenantService
from app.shared.enums import Role
from app.shared.exceptions import NotFoundError, PermissionDeniedError
from app.shared.schemas import Page

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/me", response_model=TenantOut)
async def my_tenant(user: CurrentUser, session: DbSession):
    if user.tenant_id is None:
        raise NotFoundError("You are not associated with a tenant")
    return await TenantService(session).get(user.tenant_id)


@router.post(
    "",
    response_model=TenantOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(Role.SUPER_ADMIN))],
)
async def create_tenant(payload: TenantCreate, session: DbSession):
    return await TenantService(session).create(payload)


@router.get("", response_model=Page[TenantOut], dependencies=[Depends(require_role(Role.SUPER_ADMIN))])
async def list_tenants(session: DbSession, pagination: Pagination):
    items, total = await TenantService(session).list(
        offset=pagination.offset, limit=pagination.limit
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/{tenant_id}", response_model=TenantOut)
async def get_tenant(tenant_id: uuid.UUID, user: CurrentUser, session: DbSession):
    if user.role != Role.SUPER_ADMIN and user.tenant_id != tenant_id:
        raise PermissionDeniedError("Cannot access another tenant")
    return await TenantService(session).get(tenant_id)


@router.patch(
    "/{tenant_id}",
    response_model=TenantOut,
    dependencies=[Depends(require_role(Role.SUPER_ADMIN, Role.TENANT_ADMIN))],
)
async def update_tenant(
    tenant_id: uuid.UUID, payload: TenantUpdate, user: CurrentUser, session: DbSession
):
    if user.role == Role.TENANT_ADMIN and user.tenant_id != tenant_id:
        raise PermissionDeniedError("Cannot modify another tenant")
    return await TenantService(session).update(tenant_id, payload)
