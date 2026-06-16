"""Meta WhatsApp Cloud API client + webhook helpers.

Without ``WHATSAPP_ACCESS_TOKEN`` set, outbound messages are logged instead of
sent so the integration is fully testable offline.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class InboundMessage:
    wa_phone: str
    profile_name: str | None
    text: str
    message_id: str
    business_phone_number_id: str | None
    image_id: str | None = None


# --------------------------------------------------------------------------- #
# Outbound
# --------------------------------------------------------------------------- #
async def send_text(*, to: str, body: str) -> tuple[bool, str | None]:
    if not settings.whatsapp_enabled:
        logger.info("whatsapp_stub_send", to=to, body=body)
        return True, None

    url = (
        f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
        return True, None
    except Exception as exc:  # noqa: BLE001
        logger.warning("whatsapp_send_failed", error=str(exc))
        return False, str(exc)


# --------------------------------------------------------------------------- #
# Webhook verification
# --------------------------------------------------------------------------- #
def verify_webhook(mode: str | None, token: str | None, challenge: str | None) -> str | None:
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return challenge
    return None


def verify_signature(payload: bytes, signature_header: str | None) -> bool:
    """Validate ``X-Hub-Signature-256``. Skips when no app secret is configured."""
    if not settings.WHATSAPP_APP_SECRET:
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header.split("=", 1)[1])


# --------------------------------------------------------------------------- #
# Inbound parsing
# --------------------------------------------------------------------------- #
def parse_inbound(payload: dict) -> list[InboundMessage]:
    messages: list[InboundMessage] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            metadata = value.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id")
            contacts = {c["wa_id"]: c.get("profile", {}).get("name") for c in value.get("contacts", [])}
            for msg in value.get("messages", []):
                wa_phone = msg.get("from")
                mtype = msg.get("type")
                text = ""
                image_id = None
                if mtype == "text":
                    text = msg.get("text", {}).get("body", "")
                elif mtype == "image":
                    image_id = msg.get("image", {}).get("id")
                    text = msg.get("image", {}).get("caption", "")
                else:
                    text = msg.get("button", {}).get("text", "") or ""
                messages.append(
                    InboundMessage(
                        wa_phone=wa_phone,
                        profile_name=contacts.get(wa_phone),
                        text=text,
                        message_id=msg.get("id", ""),
                        business_phone_number_id=phone_number_id,
                        image_id=image_id,
                    )
                )
    return messages
