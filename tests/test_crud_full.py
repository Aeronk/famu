"""Full-CRUD coverage: update + delete across child resources."""

from __future__ import annotations

from tests.conftest import auth_header, register_tenant


async def _token(client) -> str:
    data = await register_tenant(client, "crudfull", "crudfull@example.com")
    return auth_header(data["tokens"]["access_token"])


async def test_finance_update_delete(client):
    h = await _token(client)
    exp = (await client.post("/api/v1/finance/expenses", json={"category": "seed", "amount": 100}, headers=h)).json()
    upd = await client.patch(f"/api/v1/finance/expenses/{exp['id']}", json={"amount": 250}, headers=h)
    assert upd.json()["amount"] == 250.0
    d = await client.delete(f"/api/v1/finance/expenses/{exp['id']}", headers=h)
    assert d.status_code == 200
    assert (await client.get("/api/v1/finance/expenses", headers=h)).json()["total"] == 0


async def test_crop_input_and_harvest_crud(client):
    h = await _token(client)
    farm = (await client.post("/api/v1/farms", json={"name": "Main Farm"}, headers=h)).json()
    cycle = (await client.post("/api/v1/crops/cycles", json={"farm_id": farm["id"], "crop_type": "maize", "area_ha": 1}, headers=h)).json()
    inp = (await client.post(f"/api/v1/crops/cycles/{cycle['id']}/inputs", json={"type": "fertilizer", "name": "AN"}, headers=h)).json()
    upd = await client.patch(f"/api/v1/crops/inputs/{inp['id']}", json={"quantity": 50, "unit": "kg"}, headers=h)
    assert upd.json()["quantity"] == 50
    assert (await client.delete(f"/api/v1/crops/inputs/{inp['id']}", headers=h)).status_code == 200


async def test_livestock_vaccination_crud(client):
    h = await _token(client)
    vac = (await client.post("/api/v1/livestock/vaccinations", json={"head_count": 5}, headers=h)).json()
    assert (await client.get("/api/v1/livestock/vaccinations", headers=h)).json()["total"] == 1
    upd = await client.patch(f"/api/v1/livestock/vaccinations/{vac['id']}", json={"vaccine": "Blackleg"}, headers=h)
    assert upd.json()["vaccine"] == "Blackleg"
    assert (await client.delete(f"/api/v1/livestock/vaccinations/{vac['id']}", headers=h)).status_code == 200
    assert (await client.get("/api/v1/livestock/vaccinations", headers=h)).json()["total"] == 0
