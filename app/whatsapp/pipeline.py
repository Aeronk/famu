"""WhatsApp event-processing pipeline.

parse -> resolve user/tenant -> idempotency -> (multi-turn | agent) -> persist -> reply.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.graph import run_agent
from app.ai.agents.schemas import AgentDeps
from app.ai.models import AIConversation, AIMessage
from app.core.logging import get_logger
from app.modules.auth.repository import UserRepo
from app.modules.auth.service import AuthService
from app.modules.livestock.repository import VaccinationRepo
from app.modules.tenants.models import Tenant
from app.shared.enums import Language, MessageRole
from app.shared.i18n import detect_language, translate
from app.whatsapp.client import InboundMessage, send_text
from app.whatsapp.models import WhatsAppContact

logger = get_logger(__name__)

_NEW_COMMAND_HINTS = ("plant", "dyara", "tshala", "vaccinat", "harvest", "goho", "spent", "bought")


async def _tenant_by_phone_number_id(session: AsyncSession, phone_number_id: str):
    """Map a WhatsApp Business phone_number_id -> tenant via tenant.settings.

    Uses a JSON operator on Postgres; falls back to an in-Python scan on SQLite.
    """
    from app.database.session import engine

    if engine.dialect.name == "postgresql":
        stmt = select(Tenant).where(
            Tenant.settings["whatsapp_phone_number_id"].astext == phone_number_id
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    tenants = (await session.execute(select(Tenant))).scalars().all()
    return next(
        (t for t in tenants if (t.settings or {}).get("whatsapp_phone_number_id") == phone_number_id),
        None,
    )


async def _resolve_tenant_user(session: AsyncSession, msg: InboundMessage):
    users = UserRepo(session)
    user = await users.by_phone(msg.wa_phone)
    if user and user.tenant_id:
        return user.tenant_id, user

    # Fall back to mapping the business number -> tenant, then auto-onboard.
    if msg.business_phone_number_id:
        tenant = await _tenant_by_phone_number_id(session, msg.business_phone_number_id)
        if tenant:
            user = await AuthService(session).get_or_create_farmer_by_phone(
                phone_number=msg.wa_phone,
                tenant_id=tenant.id,
                full_name=msg.profile_name or "",
                language=detect_language(msg.text),
            )
            return tenant.id, user
    return None, None


async def _get_contact(session: AsyncSession, tenant_id, msg: InboundMessage, user_id) -> WhatsAppContact:
    repo_stmt = select(WhatsAppContact).where(WhatsAppContact.wa_phone == msg.wa_phone)
    contact = (await session.execute(repo_stmt)).scalar_one_or_none()
    if contact is None:
        contact = WhatsAppContact(
            tenant_id=tenant_id, user_id=user_id, wa_phone=msg.wa_phone,
            profile_name=msg.profile_name, state={},
        )
        session.add(contact)
        await session.flush()
    return contact


async def _conversation(session: AsyncSession, tenant_id, user_id) -> AIConversation:
    stmt = (
        select(AIConversation)
        .where(AIConversation.tenant_id == str(tenant_id), AIConversation.user_id == user_id)
        .order_by(AIConversation.created_at.desc())
        .limit(1)
    )
    conv = (await session.execute(stmt)).scalar_one_or_none()
    if conv is None:
        conv = AIConversation(tenant_id=tenant_id, user_id=user_id, channel="whatsapp")
        session.add(conv)
        await session.flush()
    return conv


async def process_inbound(session: AsyncSession, msg: InboundMessage) -> str | None:
    if not msg.wa_phone:
        return None

    tenant_id, user = await _resolve_tenant_user(session, msg)
    if tenant_id is None:
        reply = translate("need_registration", detect_language(msg.text))
        await send_text(to=msg.wa_phone, body=reply)
        return reply

    contact = await _get_contact(session, tenant_id, msg, user.id if user else None)

    # Idempotency: ignore duplicate webhook deliveries.
    if msg.message_id and contact.last_message_id == msg.message_id:
        logger.info("whatsapp_duplicate_ignored", message_id=msg.message_id)
        return None
    contact.last_message_id = msg.message_id
    contact.last_seen_at = datetime.now(UTC)
    if msg.profile_name:
        contact.profile_name = msg.profile_name

    lang = detect_language(msg.text)

    # ---- Multi-turn: completing a pending vaccination ("Which vaccine?") ----
    awaiting = contact.state.get("awaiting")
    if awaiting == "vaccine" and not any(h in msg.text.lower() for h in _NEW_COMMAND_HINTS):
        record_id = contact.state.get("record_id")
        vac = await VaccinationRepo(session, tenant_id).get(record_id) if record_id else None
        if vac:
            vac.vaccine = msg.text.strip()
            contact.state = {}
            reply = translate("vaccination_recorded", lang, count=vac.head_count)
            await send_text(to=msg.wa_phone, body=reply)
            return reply

    # ---- Run the agent ----
    deps = AgentDeps(session=session, tenant_id=tenant_id, user_id=user.id if user else None)
    result = await run_agent(msg.text, deps)

    # Persist conversation history.
    conv = await _conversation(session, tenant_id, user.id if user else None)
    conv.last_message_at = datetime.now(UTC)
    session.add(AIMessage(tenant_id=tenant_id, conversation_id=conv.id, role=MessageRole.USER,
                          content=msg.text, language=Language(result.language), intent=result.intent,
                          entities=result.entities))
    session.add(AIMessage(tenant_id=tenant_id, conversation_id=conv.id, role=MessageRole.ASSISTANT,
                          content=result.reply, language=Language(result.language)))

    # Capture the WhatsApp message as an NLU training example.
    from app.datasets.service import DatasetService

    await DatasetService(session, tenant_id).record_nlu(
        text=msg.text, intent=result.intent, entities=result.entities,
        channel="whatsapp", created_by=user.id if user else None,
    )

    # Track a pending follow-up so the next message can complete it.
    if result.follow_up and result.intent == "record_vaccination" and result.record_id:
        contact.state = {"awaiting": "vaccine", "record_id": result.record_id}
    else:
        contact.state = {}

    await send_text(to=msg.wa_phone, body=result.reply)
    return result.reply
