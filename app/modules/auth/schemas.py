from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.modules.tenants.schemas import TenantCreate, TenantOut
from app.shared.enums import Language, Role
from app.shared.schemas import ORMModel


class RegisterTenantRequest(BaseModel):
    """Self-service onboarding: creates a tenant + its first Tenant Admin."""

    tenant: TenantCreate
    admin_email: EmailStr
    admin_password: str = Field(min_length=8, max_length=128)
    admin_full_name: str = Field(min_length=2, max_length=160)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    phone_number: str | None = Field(default=None, max_length=32)
    full_name: str = Field(min_length=2, max_length=160)
    role: Role = Role.FARMER
    language: Language = Language.EN


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: Role | None = None
    language: Language | None = None
    is_active: bool | None = None
    phone_number: str | None = None


class UserOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    email: str | None
    phone_number: str | None
    full_name: str
    role: Role
    language: Language
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime


class RegisterTenantResponse(BaseModel):
    tenant: TenantOut
    admin: UserOut
    tokens: TokenPair
