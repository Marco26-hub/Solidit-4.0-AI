from __future__ import annotations

import uuid

from app.billing.service import _tier_for_plan


def test_plan_tier_mapping():
    assert _tier_for_plan("trace") == "trace"
    assert _tier_for_plan("vision") == "vision"
    assert _tier_for_plan(None) == "trace"
    assert _tier_for_plan("bogus") == "trace"


async def _register(client, email, company):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "company_name": company},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_checkout_requires_stripe_config(client, require_db):
    # Stripe is not configured in tests -> checkout must fail cleanly (no 500)
    reg = await _register(client, f"bill-{uuid.uuid4().hex[:8]}@example.com", "Bill Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}
    r = await client.post("/api/v1/billing/checkout", json={"plan": "trace"}, headers=h)
    assert r.status_code == 400, r.text
    assert "no_price" in r.text or "stripe" in r.text.lower()


async def test_webhook_ignored_without_secret(client, require_db):
    r = await client.post("/api/v1/billing/webhook", content=b"{}")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ignored"


async def test_invalid_plan_rejected_by_schema(client, require_db):
    reg = await _register(client, f"bill2-{uuid.uuid4().hex[:8]}@example.com", "Bill2 Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}
    r = await client.post("/api/v1/billing/checkout", json={"plan": "gold"}, headers=h)
    assert r.status_code == 422, r.text  # pattern validation
