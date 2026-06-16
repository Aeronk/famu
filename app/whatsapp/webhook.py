"""WhatsApp webhook: GET verification + POST message receipt."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request, Response, status

from app.api.deps import DbSession
from app.core.logging import get_logger
from app.whatsapp.client import parse_inbound, verify_signature, verify_webhook
from app.whatsapp.pipeline import process_inbound

logger = get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["whatsapp"])


@router.get("/whatsapp")
async def verify(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
):
    challenge = verify_webhook(hub_mode, hub_verify_token, hub_challenge)
    if challenge is None:
        return Response(status_code=status.HTTP_403_FORBIDDEN, content="verification failed")
    return Response(content=challenge, media_type="text/plain")


@router.post("/whatsapp")
async def receive(request: Request, session: DbSession):
    raw = await request.body()
    if not verify_signature(raw, request.headers.get("X-Hub-Signature-256")):
        return Response(status_code=status.HTTP_403_FORBIDDEN, content="invalid signature")

    payload = await request.json()
    replies = []
    for message in parse_inbound(payload):
        try:
            reply = await process_inbound(session, message)
            replies.append({"to": message.wa_phone, "reply": reply})
        except Exception as exc:  # noqa: BLE001 — always 200 so Meta doesn't retry-storm
            logger.exception("whatsapp_pipeline_error", error=str(exc))
    # Meta requires a prompt 200; processing results are returned for debugging.
    return {"status": "received", "processed": replies}
