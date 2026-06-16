from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import CurrentUser, DbSession, Pagination, require_role
from app.modules.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterTenantRequest,
    RegisterTenantResponse,
    TokenPair,
    UserCreate,
    UserOut,
)
from app.modules.auth.service import AuthService
from app.shared.enums import Role
from app.shared.schemas import Message

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    ua = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    return ua, ip


@router.post("/register-tenant", response_model=RegisterTenantResponse, status_code=status.HTTP_201_CREATED)
async def register_tenant(payload: RegisterTenantRequest, session: DbSession):
    tenant, admin, tokens = await AuthService(session).register_tenant(payload)
    return RegisterTenantResponse(
        tenant=tenant, admin=admin, tokens=tokens
    )


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, request: Request, session: DbSession):
    ua, ip = _client_meta(request)
    return await AuthService(session).login(payload, ua=ua, ip=ip)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, request: Request, session: DbSession):
    ua, ip = _client_meta(request)
    return await AuthService(session).refresh(payload.refresh_token, ua=ua, ip=ip)


@router.post("/logout", response_model=Message)
async def logout(payload: RefreshRequest, session: DbSession):
    await AuthService(session).logout(payload.refresh_token)
    return Message(message="Logged out")


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser):
    return user


@router.post(
    "/users",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(Role.TENANT_ADMIN, Role.FARM_MANAGER))],
)
async def create_user(payload: UserCreate, user: CurrentUser, session: DbSession):
    return await AuthService(session).create_user(user.tenant_id, payload)


@router.get(
    "/users",
    response_model=list[UserOut],
    dependencies=[Depends(require_role(Role.TENANT_ADMIN, Role.FARM_MANAGER))],
)
async def list_users(user: CurrentUser, session: DbSession, pagination: Pagination):
    return await AuthService(session).users.list_for_tenant(
        str(user.tenant_id), offset=pagination.offset, limit=pagination.limit
    )
