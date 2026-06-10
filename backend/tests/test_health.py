from __future__ import annotations


async def test_healthz(client):
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body


async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["docs"] == "/docs"
