"""Auth, refresh-token rotation, and multi-tenant isolation."""

from __future__ import annotations

from tests.conftest import auth_header, register_tenant


async def test_register_and_login(client):
    data = await register_tenant(client, "alpha-farm", "alpha@example.com")
    assert data["tenant"]["slug"] == "alpha-farm"
    assert data["admin"]["role"] == "tenant_admin"
    assert data["tokens"]["access_token"]

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "alpha@example.com", "password": "Password123"},
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_refresh_rotation(client):
    data = await register_tenant(client, "beta-farm", "beta@example.com")
    refresh = data["tokens"]["refresh_token"]

    r1 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r1.status_code == 200

    # Old refresh token is now revoked (rotation).
    r2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 401


async def test_me_requires_auth(client):
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_tenant_isolation(client):
    a = await register_tenant(client, "tenant-a", "a@example.com")
    b = await register_tenant(client, "tenant-b", "b@example.com")
    a_token = a["tokens"]["access_token"]
    b_token = b["tokens"]["access_token"]

    # Tenant A creates a farm.
    resp = await client.post(
        "/api/v1/farms",
        json={"name": "A Field", "size_ha": 3},
        headers=auth_header(a_token),
    )
    assert resp.status_code == 201, resp.text
    farm_id = resp.json()["id"]

    # Tenant A sees it.
    a_list = await client.get("/api/v1/farms", headers=auth_header(a_token))
    assert a_list.json()["total"] == 1

    # Tenant B sees NONE of A's data.
    b_list = await client.get("/api/v1/farms", headers=auth_header(b_token))
    assert b_list.json()["total"] == 0

    # Tenant B cannot fetch A's farm by id.
    cross = await client.get(f"/api/v1/farms/{farm_id}", headers=auth_header(b_token))
    assert cross.status_code == 404
