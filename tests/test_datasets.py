"""AI training-data capture, curation and export."""

from __future__ import annotations

from tests.conftest import auth_header, register_tenant


async def _setup(client):
    data = await register_tenant(client, "data-farm", "data@example.com")
    h = auth_header(data["tokens"]["access_token"])
    farm = (await client.post("/api/v1/farms", json={"name": "F1"}, headers=h)).json()
    cycle = (
        await client.post(
            "/api/v1/crops/cycles",
            json={"farm_id": farm["id"], "crop_type": "maize", "area_ha": 2, "planting_date": "2026-01-15"},
            headers=h,
        )
    ).json()
    return h, cycle


async def test_yield_example_auto_captured_on_harvest(client):
    h, cycle = await _setup(client)
    await client.post(
        f"/api/v1/crops/cycles/{cycle['id']}/harvests",
        json={"quantity": 8000, "unit": "kg", "harvest_date": "2026-05-01"},
        headers=h,
    )
    resp = await client.get("/api/v1/datasets/examples?dataset=yield", headers=h)
    body = resp.json()
    assert body["total"] == 1
    ex = body["items"][0]
    assert ex["features"]["crop"] == "maize"
    assert ex["label"]["yield_tonnes"] == 8.0          # 8000 kg -> 8 t
    assert ex["label"]["yield_per_ha_t"] == 4.0        # 8 t / 2 ha


async def test_build_yield_dataset(client):
    h, cycle = await _setup(client)
    await client.post(
        f"/api/v1/crops/cycles/{cycle['id']}/harvests",
        json={"quantity": 5000, "unit": "kg"}, headers=h,
    )
    r = await client.post("/api/v1/datasets/build/yield", headers=h)
    assert r.json()["examples_built"] >= 1


async def test_nlu_example_captured_from_chat(client):
    data = await register_tenant(client, "nlu-farm", "nlu@example.com")
    h = auth_header(data["tokens"]["access_token"])
    await client.post("/api/v1/ai/chat", json={"text": "I planted 2 hectares of maize", "channel": "mobile"}, headers=h)

    resp = await client.get("/api/v1/datasets/examples?dataset=nlu_intent", headers=h)
    body = resp.json()
    assert body["total"] == 1
    ex = body["items"][0]
    assert ex["channel"] == "mobile"
    assert ex["features"]["text"].startswith("I planted")
    assert ex["label"]["intent"] == "record_planting"


async def test_verify_and_export(client):
    h, cycle = await _setup(client)
    await client.post(
        f"/api/v1/crops/cycles/{cycle['id']}/harvests",
        json={"quantity": 3000, "unit": "kg"}, headers=h,
    )
    ex_id = (await client.get("/api/v1/datasets/examples?dataset=yield", headers=h)).json()["items"][0]["id"]

    # Verify (human-in-the-loop)
    patched = await client.patch(f"/api/v1/datasets/examples/{ex_id}", json={"status": "verified"}, headers=h)
    assert patched.json()["status"] == "verified"

    # Stats reflect the verified example
    stats = (await client.get("/api/v1/datasets", headers=h)).json()
    yield_stat = next(d for d in stats["datasets"] if d["dataset"] == "yield")
    assert yield_stat["verified"] == 1

    # Export JSONL
    exp = await client.get("/api/v1/datasets/export?dataset=yield&format=jsonl", headers=h)
    assert exp.status_code == 200
    assert "feature.crop" in exp.text and "label.yield_tonnes" in exp.text
