"""Image/file upload attached to records."""

from __future__ import annotations

from tests.conftest import auth_header, register_tenant

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64  # minimal fake image payload


async def test_upload_list_get_delete(client):
    data = await register_tenant(client, "media-farm", "media@example.com")
    h = auth_header(data["tokens"]["access_token"])
    farm = (await client.post("/api/v1/farms", json={"name": "Photo Farm"}, headers=h)).json()

    # Upload a photo attached to the farm
    resp = await client.post(
        "/api/v1/media",
        files={"file": ("leaf.png", PNG, "image/png")},
        data={"ref_type": "farm", "ref_id": farm["id"], "caption": "north field"},
        headers=h,
    )
    assert resp.status_code == 201, resp.text
    att = resp.json()
    assert att["kind"] == "image"
    assert att["caption"] == "north field"

    # List attachments for the farm
    lst = await client.get(f"/api/v1/media?ref_type=farm&ref_id={farm['id']}", headers=h)
    assert lst.json()["total"] == 1

    # Fetch the binary
    f = await client.get(f"/api/v1/media/{att['id']}/file", headers=h)
    assert f.status_code == 200
    assert f.content == PNG

    # Delete
    d = await client.delete(f"/api/v1/media/{att['id']}", headers=h)
    assert d.status_code == 200
    lst2 = await client.get(f"/api/v1/media?ref_type=farm&ref_id={farm['id']}", headers=h)
    assert lst2.json()["total"] == 0


async def test_upload_requires_auth(client):
    resp = await client.post("/api/v1/media", files={"file": ("x.png", PNG, "image/png")})
    assert resp.status_code == 401
