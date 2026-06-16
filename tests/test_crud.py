"""CRUD + computed reports across the core modules."""

from __future__ import annotations

from tests.conftest import auth_header, register_tenant


async def _token(client) -> str:
    data = await register_tenant(client, "crud-farm", "crud@example.com")
    return data["tokens"]["access_token"]


async def test_crop_cycle_timeline(client):
    token = await _token(client)
    h = auth_header(token)

    farm = (await client.post("/api/v1/farms", json={"name": "Main"}, headers=h)).json()
    cycle = (
        await client.post(
            "/api/v1/crops/cycles",
            json={"farm_id": farm["id"], "crop_type": "maize", "area_ha": 2, "planting_date": "2026-01-15"},
            headers=h,
        )
    ).json()
    await client.post(
        f"/api/v1/crops/cycles/{cycle['id']}/inputs",
        json={"type": "fertilizer", "name": "Compound D", "quantity": 250, "unit": "kg", "applied_date": "2026-01-16"},
        headers=h,
    )
    await client.post(
        f"/api/v1/crops/cycles/{cycle['id']}/harvests",
        json={"quantity": 8000, "unit": "kg", "harvest_date": "2026-05-01"},
        headers=h,
    )

    timeline = (await client.get(f"/api/v1/crops/cycles/{cycle['id']}/timeline", headers=h)).json()
    kinds = {e["kind"] for e in timeline["events"]}
    assert {"planting", "input", "harvest"} <= kinds


async def test_livestock_and_herd_analytics(client):
    token = await _token(client)
    h = auth_header(token)
    farm = (await client.post("/api/v1/farms", json={"name": "Ranch"}, headers=h)).json()

    await client.post(
        "/api/v1/livestock",
        json={"farm_id": farm["id"], "species": "cattle", "tag_number": "C001", "sex": "female", "weight_kg": 320},
        headers=h,
    )
    await client.post(
        "/api/v1/livestock/vaccinations",
        json={"head_count": 5, "vaccine": "Blackleg", "next_due_date": "2026-07-01"},
        headers=h,
    )

    analytics = (await client.get("/api/v1/livestock/analytics", headers=h)).json()
    assert analytics["total_head"] == 1
    assert analytics["by_species"]["cattle"] == 1


async def test_finance_reports(client):
    token = await _token(client)
    h = auth_header(token)

    await client.post("/api/v1/finance/incomes", json={"source": "maize sales", "amount": 1000, "txn_date": "2026-05-02"}, headers=h)
    await client.post("/api/v1/finance/expenses", json={"category": "seed", "amount": 300, "txn_date": "2026-01-10"}, headers=h)

    prof = (await client.get("/api/v1/finance/reports/profitability", headers=h)).json()
    assert prof["total_income"] == 1000.0
    assert prof["total_expense"] == 300.0
    assert prof["gross_profit"] == 700.0

    cashflow = (await client.get("/api/v1/finance/reports/cashflow", headers=h)).json()
    assert cashflow["net"] == 700.0
    assert len(cashflow["periods"]) == 2


async def test_tobacco_profitability(client):
    token = await _token(client)
    h = auth_header(token)
    farm = (await client.post("/api/v1/farms", json={"name": "Tobacco Farm"}, headers=h)).json()
    cycle = (
        await client.post("/api/v1/tobacco/cycles", json={"farm_id": farm["id"], "area_ha": 2}, headers=h)
    ).json()

    await client.post(f"/api/v1/tobacco/cycles/{cycle['id']}/reaping", json={"mass_kg": 2000}, headers=h)
    await client.post(f"/api/v1/tobacco/cycles/{cycle['id']}/curing", json={"mass_kg": 1600}, headers=h)
    await client.post(
        f"/api/v1/tobacco/cycles/{cycle['id']}/deliveries",
        json={"mass_kg": 1500, "price_per_kg": 3.0, "deductions": 200},
        headers=h,
    )

    report = (await client.get(f"/api/v1/tobacco/cycles/{cycle['id']}/profitability", headers=h)).json()
    assert report["gross_revenue"] == 4500.0
    assert report["net_revenue"] == 4300.0
    assert report["total_reaped_kg"] == 2000.0


async def test_rbac_viewer_cannot_create(client):
    data = await register_tenant(client, "rbac-farm", "rbac@example.com")
    admin = auth_header(data["tokens"]["access_token"])
    # Admin creates a viewer.
    await client.post(
        "/api/v1/auth/users",
        json={"email": "viewer@example.com", "password": "Password123", "full_name": "View Only", "role": "viewer"},
        headers=admin,
    )
    login = await client.post("/api/v1/auth/login", json={"email": "viewer@example.com", "password": "Password123"})
    viewer = auth_header(login.json()["access_token"])

    resp = await client.post("/api/v1/farms", json={"name": "Nope"}, headers=viewer)
    assert resp.status_code == 403
