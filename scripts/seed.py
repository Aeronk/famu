"""Seed demo data: super admin, a tenant with users, a farm, market prices and
the RAG knowledge base.

Run after migrating:  python -m scripts.seed
"""

from __future__ import annotations

import asyncio
from datetime import date

from app.ai.rag.ingest import ingest_seed_knowledge
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepo
from app.modules.farms.repository import FarmRepo
from app.modules.market.models import MarketPrice
from app.modules.tenants.repository import TenantRepo
from app.shared.enums import Language, Role, TenantStatus, TenantType

SUPER_ADMIN_EMAIL = "admin@murimi.os"
TENANT_ADMIN_EMAIL = "admin@greenvalley.co"
FARM_MANAGER_EMAIL = "manager@greenvalley.co"
FARMER_PHONE = "+263771234567"
DEFAULT_PASSWORD = "ChangeMe12345"
DEMO_PHONE_NUMBER_ID = "DEMO_PHONE_ID"


async def seed() -> None:
    async with SessionLocal() as session:
        users = UserRepo(session)
        tenants = TenantRepo(session)

        # ---- Super Admin (platform-level, no tenant) ----
        if not await users.by_email(SUPER_ADMIN_EMAIL):
            session.add(
                User(
                    email=SUPER_ADMIN_EMAIL,
                    hashed_password=hash_password(DEFAULT_PASSWORD),
                    full_name="Platform Super Admin",
                    role=Role.SUPER_ADMIN,
                )
            )

        # ---- Demo tenant ----
        tenant = await tenants.find_one(slug="green-valley")
        if not tenant:
            tenant = await tenants.create(
                name="Green Valley Cooperative",
                slug="green-valley",
                type=TenantType.COOPERATIVE,
                status=TenantStatus.ACTIVE,
                plan="pro",
                country="Zimbabwe",
                settings={"whatsapp_phone_number_id": DEMO_PHONE_NUMBER_ID},
            )

        if not await users.by_email(TENANT_ADMIN_EMAIL):
            session.add(
                User(
                    tenant_id=tenant.id,
                    email=TENANT_ADMIN_EMAIL,
                    hashed_password=hash_password(DEFAULT_PASSWORD),
                    full_name="Rumbidzai Admin",
                    role=Role.TENANT_ADMIN,
                )
            )
        if not await users.by_email(FARM_MANAGER_EMAIL):
            session.add(
                User(
                    tenant_id=tenant.id,
                    email=FARM_MANAGER_EMAIL,
                    hashed_password=hash_password(DEFAULT_PASSWORD),
                    full_name="Farai Manager",
                    role=Role.FARM_MANAGER,
                )
            )

        farmer = await users.by_phone(FARMER_PHONE)
        if not farmer:
            farmer = User(
                tenant_id=tenant.id,
                phone_number=FARMER_PHONE,
                full_name="Tendai Moyo",
                role=Role.FARMER,
                language=Language.EN,
            )
            session.add(farmer)
            await session.flush()

        # ---- Demo farm owned by the farmer ----
        farms = FarmRepo(session, tenant.id)
        if not await farms.find_one(name="Tendai's Field"):
            await farms.create(
                name="Tendai's Field",
                owner_user_id=farmer.id,
                gps_lat=-17.83,
                gps_lng=31.05,
                province="Mashonaland East",
                district="Goromonzi",
                ward="12",
                village="Juru",
                soil_type="sandy loam",
                water_source="borehole",
                irrigation_type="drip",
                size_ha=4.5,
            )

        # ---- Market prices (global reference data) ----
        existing_prices = await session.execute(
            MarketPrice.__table__.select().limit(1)
        )
        if existing_prices.first() is None:
            for commodity, price in [
                ("maize", 0.30), ("tobacco", 3.0), ("soybeans", 0.60),
                ("wheat", 0.45), ("cotton", 0.70), ("groundnuts", 0.80),
            ]:
                session.add(
                    MarketPrice(
                        commodity=commodity, market="Harare", price=price,
                        currency="USD", unit="kg", price_date=date.today(),
                        source="seed",
                    )
                )

        # ---- RAG knowledge base ----
        from sqlalchemy import select

        from app.ai.rag.models import KnowledgeDocument

        has_docs = (await session.execute(select(KnowledgeDocument).limit(1))).first()
        if has_docs is None:
            count = await ingest_seed_knowledge(session)
            print(f"  ingested {count} knowledge documents")

        await session.commit()

    print("Seed complete.")
    print("  Super Admin :", SUPER_ADMIN_EMAIL, "/", DEFAULT_PASSWORD)
    print("  Tenant Admin:", TENANT_ADMIN_EMAIL, "/", DEFAULT_PASSWORD)
    print("  Farm Manager:", FARM_MANAGER_EMAIL, "/", DEFAULT_PASSWORD)
    print("  Farmer phone:", FARMER_PHONE, "(WhatsApp, no password)")


if __name__ == "__main__":
    asyncio.run(seed())
