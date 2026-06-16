from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    refresh_token_expiry,
    verify_password,
)
from app.modules.auth.models import User
from app.modules.auth.repository import RefreshTokenRepo, UserRepo
from app.modules.auth.schemas import (
    LoginRequest,
    RegisterTenantRequest,
    TokenPair,
    UserCreate,
)
from app.modules.tenants.models import Tenant
from app.modules.tenants.repository import TenantRepo
from app.shared.enums import Language, Role, TenantStatus
from app.shared.exceptions import AuthenticationError, ConflictError, NotFoundError


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepo(session)
        self.tokens = RefreshTokenRepo(session)
        self.tenants = TenantRepo(session)

    # ------------------------------------------------------------------ #
    # Onboarding
    # ------------------------------------------------------------------ #
    async def register_tenant(self, req: RegisterTenantRequest) -> tuple[Tenant, User, TokenPair]:
        if await self.tenants.find_one(slug=req.tenant.slug):
            raise ConflictError(f"Tenant slug '{req.tenant.slug}' is already taken")
        if await self.users.by_email(req.admin_email):
            raise ConflictError("Email already registered")

        tenant = await self.tenants.create(
            **req.tenant.model_dump() | {"status": TenantStatus.ACTIVE}
        )
        admin = await self.users.create(
            tenant_id=tenant.id,
            email=req.admin_email,
            hashed_password=hash_password(req.admin_password),
            full_name=req.admin_full_name,
            role=Role.TENANT_ADMIN,
        )
        tokens = await self.issue_tokens(admin)
        return tenant, admin, tokens

    # ------------------------------------------------------------------ #
    # Login / tokens
    # ------------------------------------------------------------------ #
    async def login(self, req: LoginRequest, *, ua: str | None, ip: str | None) -> TokenPair:
        user = await self.users.by_email(req.email)
        if not user or not user.hashed_password or not verify_password(req.password, user.hashed_password):
            raise AuthenticationError("Incorrect email or password")
        if not user.is_active:
            raise AuthenticationError("Account is disabled")
        user.last_login_at = datetime.now(UTC)
        return await self.issue_tokens(user, ua=ua, ip=ip)

    async def issue_tokens(
        self, user: User, *, ua: str | None = None, ip: str | None = None
    ) -> TokenPair:
        access = create_access_token(
            subject=user.id, role=user.role.value, tenant_id=user.tenant_id
        )
        raw_refresh, token_h = generate_refresh_token()
        await self.tokens.create(
            user_id=user.id,
            token_hash=token_h,
            expires_at=refresh_token_expiry(),
            user_agent=ua,
            ip_address=ip,
        )
        return TokenPair(
            access_token=access,
            refresh_token=raw_refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh(self, raw_token: str, *, ua: str | None, ip: str | None) -> TokenPair:
        record = await self.tokens.by_hash(hash_token(raw_token))
        if not record or record.revoked:
            raise AuthenticationError("Invalid refresh token")
        # SQLite returns naive datetimes even for tz-aware columns; normalize to UTC.
        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < datetime.now(UTC):
            raise AuthenticationError("Refresh token has expired")
        user = await self.users.get(record.user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User no longer active")
        record.revoked = True  # rotate
        return await self.issue_tokens(user, ua=ua, ip=ip)

    async def logout(self, raw_token: str) -> None:
        record = await self.tokens.by_hash(hash_token(raw_token))
        if record:
            record.revoked = True

    # ------------------------------------------------------------------ #
    # User management (tenant-scoped)
    # ------------------------------------------------------------------ #
    async def create_user(self, tenant_id: uuid.UUID, data: UserCreate) -> User:
        if data.email and await self.users.by_email(data.email):
            raise ConflictError("Email already registered")
        if data.phone_number and await self.users.by_phone(data.phone_number):
            raise ConflictError("Phone number already registered")
        return await self.users.create(
            tenant_id=tenant_id,
            email=data.email,
            phone_number=data.phone_number,
            hashed_password=hash_password(data.password) if data.password else None,
            full_name=data.full_name,
            role=data.role,
            language=data.language,
        )

    async def get_user(self, user_id: uuid.UUID) -> User:
        user = await self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    async def get_or_create_farmer_by_phone(
        self,
        *,
        phone_number: str,
        tenant_id: uuid.UUID,
        full_name: str = "",
        language: Language = Language.EN,
    ) -> User:
        """Used by the WhatsApp pipeline to identify/onboard farmers by phone."""
        user = await self.users.by_phone(phone_number)
        if user:
            return user
        return await self.users.create(
            tenant_id=tenant_id,
            phone_number=phone_number,
            full_name=full_name or phone_number,
            role=Role.FARMER,
            language=language,
        )
