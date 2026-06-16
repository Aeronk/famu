from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import RefreshToken, User
from app.shared.repository import BaseRepository


class UserRepo(BaseRepository[User]):
    model = User

    async def by_email(self, email: str) -> User | None:
        return await self.find_one(email=email)

    async def by_phone(self, phone_number: str) -> User | None:
        return await self.find_one(phone_number=phone_number)

    async def list_for_tenant(self, tenant_id: str, *, offset: int, limit: int) -> list[User]:
        stmt = (
            select(User)
            .where(User.tenant_id == tenant_id)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())


class RefreshTokenRepo(BaseRepository[RefreshToken]):
    model = RefreshToken

    async def by_hash(self, token_hash: str) -> RefreshToken | None:
        return await self.find_one(token_hash=token_hash)

    async def revoke_all_for_user(self, session: AsyncSession, user_id: str) -> None:
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False)
        )
        for token in (await session.execute(stmt)).scalars().all():
            token.revoked = True
