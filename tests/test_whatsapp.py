"""WhatsApp webhook: data-capture pipeline + multi-turn flow."""

from __future__ import annotations

from tests.conftest import auth_header, register_tenant

FARMER_PHONE = "263770000001"


def _webhook_payload(text: str, message_id: str) -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "PNID_TEST"},
                            "contacts": [{"wa_id": FARMER_PHONE, "profile": {"name": "Tendai"}}],
                            "messages": [
                                {"from": FARMER_PHONE, "id": message_id, "type": "text", "text": {"body": text}}
                            ],
                        }
                    }
                ]
            }
        ],
    }


async def _setup_farmer(client) -> str:
    """Register a tenant and a farmer with FARMER_PHONE; return admin token."""
    data = await register_tenant(client, "wa-farm", "wa@example.com")
    token = data["tokens"]["access_token"]
    await client.post(
        "/api/v1/auth/users",
        json={"phone_number": FARMER_PHONE, "full_name": "Tendai", "role": "farmer"},
        headers=auth_header(token),
    )
    return token


async def test_webhook_verification(client):
    resp = await client.get(
        "/webhooks/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": "murimi-verify-token", "hub.challenge": "12345"},
    )
    assert resp.status_code == 200
    assert resp.text == "12345"


async def test_planting_capture(client):
    token = await _setup_farmer(client)

    resp = await client.post("/webhooks/whatsapp", json=_webhook_payload("I planted 2 hectares of maize", "m1"))
    assert resp.status_code == 200
    reply = resp.json()["processed"][0]["reply"]
    assert "maize" in reply.lower()

    # A crop cycle now exists for the tenant.
    cycles = await client.get("/api/v1/crops/cycles", headers=auth_header(token))
    assert cycles.json()["total"] == 1
    assert cycles.json()["items"][0]["crop_type"] == "maize"


async def test_vaccination_multiturn(client):
    await _setup_farmer(client)

    r1 = await client.post("/webhooks/whatsapp", json=_webhook_payload("I vaccinated 20 cattle today", "m2"))
    reply1 = r1.json()["processed"][0]["reply"]
    assert "vaccination recorded" in reply1.lower()
    assert "?" in reply1  # follow-up question

    # Farmer answers the follow-up with the vaccine name.
    r2 = await client.post("/webhooks/whatsapp", json=_webhook_payload("Newcastle", "m3"))
    assert r2.status_code == 200


async def test_webhook_idempotency(client):
    await _setup_farmer(client)
    payload = _webhook_payload("I planted 1 hectare of soybeans", "dup-1")
    await client.post("/webhooks/whatsapp", json=payload)
    second = await client.post("/webhooks/whatsapp", json=payload)
    # Duplicate delivery is ignored (reply is None).
    assert second.json()["processed"][0]["reply"] is None
