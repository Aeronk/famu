"""AI advisory/RAG, predictions, simulations and dashboards over HTTP."""

from __future__ import annotations

from app.ai.rag.ingest import ingest_seed_knowledge
from tests.conftest import auth_header, register_tenant


async def _token(client) -> str:
    data = await register_tenant(client, "ai-farm", "ai@example.com")
    return data["tokens"]["access_token"]


async def test_predictions(client):
    h = auth_header(await _token(client))

    y = await client.post("/api/v1/predictions/yield", json={"crop": "maize", "area": 2, "rainfall_mm": 650}, headers=h)
    assert y.status_code == 200
    assert y.json()["output"]["expected_yield"] > 0

    d = await client.post("/api/v1/predictions/disease", json={"crop": "tobacco", "humidity": 90, "rainfall_mm": 25}, headers=h)
    assert d.json()["output"]["risk"] in ("LOW", "MEDIUM", "HIGH")

    r = await client.post("/api/v1/predictions/revenue", json={"crop": "maize", "expected_yield": 10, "costs": 500}, headers=h)
    assert r.json()["output"]["profit"] == 2500.0


async def test_simulation(client):
    h = auth_header(await _token(client))
    resp = await client.post(
        "/api/v1/simulations/run",
        json={
            "crop": "maize", "area": 2, "rainfall_mm": 600, "price_per_tonne": 300, "costs": 400,
            "scenario": {"new_crop": "vegetables", "rainfall_delta_pct": -20},
        },
        headers=h,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["baseline"]["crop"] == "maize"
    assert body["scenario"]["crop"] == "vegetables"


async def test_recommendations(client):
    h = auth_header(await _token(client))
    plant = await client.get("/api/v1/ai/recommendations/planting", params={"crop": "maize"}, headers=h)
    assert "window" in plant.json()
    vac = await client.get("/api/v1/ai/recommendations/vaccination", params={"species": "cattle"}, headers=h)
    assert len(vac.json()["schedule"]) > 0


async def test_advisory_uses_rag(client, db):
    # Ingest knowledge into the test DB before asking.
    async with db() as session:
        await ingest_seed_knowledge(session)
        await session.commit()

    h = auth_header(await _token(client))
    resp = await client.post(
        "/api/v1/ai/ask",
        json={"question": "When should I plant maize and what fertilizer?"},
        headers=h,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "answer" in body
    assert len(body["sources"]) >= 1  # RAG retrieved knowledge chunks


async def test_dashboards(client):
    h = auth_header(await _token(client))
    for path in ("overview", "yields", "weather", "finances", "livestock"):
        resp = await client.get(f"/api/v1/dashboard/{path}", headers=h)
        assert resp.status_code == 200, f"{path}: {resp.text}"


async def test_vision_stub(client):
    h = auth_header(await _token(client))
    resp = await client.post(
        "/api/v1/ai/analyze-image",
        json={"image_url": "https://example.com/leaf.jpg", "analysis_type": "crop_disease"},
        headers=h,
    )
    assert resp.status_code == 200
    assert len(resp.json()["result"]["findings"]) >= 1
