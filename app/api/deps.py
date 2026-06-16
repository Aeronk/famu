"""Shared FastAPI dependencies: DB session, auth, RBAC, tenant scoping."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import has_permission, is_super_admin
from app.core.security import decode_access_token
from app.database.session import get_session
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepo
from app.shared.enums import Role
from app.shared.exceptions import AuthenticationError, PermissionDeniedError, TenantResolutionError
from app.shared.schemas import PaginationParams

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: DbSession,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if creds is None:
        raise AuthenticationError("Not authenticated")
    payload = decode_access_token(creds.credentials)
    user = await UserRepo(session).get(payload["sub"])
    if user is None or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: Role):
    async def _dep(user: CurrentUser) -> User:
        if user.role not in roles and not is_super_admin(user.role):
            raise PermissionDeniedError(
                f"Requires one of roles: {', '.join(r.value for r in roles)}"
            )
        return user

    return _dep


def require_perm(permission: str):
    async def _dep(user: CurrentUser) -> User:
        if not has_permission(user.role, permission):
            raise PermissionDeniedError(f"Missing permission: {permission}")
        return user

    return _dep


async def get_tenant_id(
    user: CurrentUser,
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
) -> uuid.UUID:
    """Resolve the active tenant.

    Regular users are bound to their own tenant. Super Admin may target any
    tenant by supplying the ``X-Tenant-ID`` header.
    """
    if is_super_admin(user.role):
        if x_tenant_id:
            return uuid.UUID(x_tenant_id)
        raise TenantResolutionError("Super Admin must supply X-Tenant-ID for tenant-scoped routes")
    if user.tenant_id is None:
        raise TenantResolutionError("User is not associated with a tenant")
    return user.tenant_id


TenantId = Annotated[uuid.UUID, Depends(get_tenant_id)]


def get_pagination(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


Pagination = Annotated[PaginationParams, Depends(get_pagination)]
