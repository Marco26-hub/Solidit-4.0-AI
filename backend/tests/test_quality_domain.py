from __future__ import annotations

import uuid

from app.test_jobs.service import evaluate_pass_fail


# ── Pure evaluation (no DB) ─────────────────────────────────────────────────────
def _rule(**kw):
    base = {
        "test_method_code": "ISO_105_X12",
        "fiber_code": "cotton",
        "max_delta_e": 1.0,
        "min_gray_scale_grade": 4.0,
        "severity": "blocking",
    }
    base.update(kw)
    return base


def test_eval_passes_within_limits():
    v = evaluate_pass_fail(
        [_rule()], "ISO_105_X12", {"cotton": {"delta_e": 0.5, "gray_scale_grade": 4.5}}
    )
    assert v["evaluated"] is True
    assert v["overall_pass"] is True
    assert v["violations"] == []


def test_eval_fails_on_delta_e():
    v = evaluate_pass_fail(
        [_rule(min_gray_scale_grade=None)], "ISO_105_X12", {"cotton": {"delta_e": 2.5}}
    )
    assert v["overall_pass"] is False
    assert v["violations"][0]["metric"] == "delta_e"


def test_eval_warning_does_not_fail():
    v = evaluate_pass_fail(
        [_rule(min_gray_scale_grade=None, severity="warning")],
        "ISO_105_X12",
        {"cotton": {"delta_e": 2.5}},
    )
    assert v["overall_pass"] is True  # warning recorded but not blocking
    assert v["violations"]


def test_eval_no_rules_is_inconclusive():
    v = evaluate_pass_fail([], "ISO_105_X12", {"cotton": {"delta_e": 0.1}})
    assert v["evaluated"] is False
    assert v["overall_pass"] is False


def test_eval_fiber_code_none_applies_to_all_fibers():
    v = evaluate_pass_fail(
        [_rule(fiber_code=None, min_gray_scale_grade=None)],
        "ISO_105_X12",
        {"wool": {"delta_e": 0.2}},
    )
    assert v["overall_pass"] is True


# ── Full Trace flow (requires Postgres) ─────────────────────────────────────────
async def _register(client, email, company):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "company_name": company},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_trace_quality_flow(client, require_db):
    reg = await _register(client, f"q-{uuid.uuid4().hex[:8]}@example.com", "QC Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}

    # brand spec + acceptance rule
    r = await client.post(
        "/api/v1/brand-specifications",
        json={
            "brand_name": "Brand X",
            "rules": [
                {
                    "test_method_code": "ISO_105_X12",
                    "fiber_code": "cotton",
                    "max_delta_e": 1.0,
                    "min_gray_scale_grade": 4.0,
                    "severity": "blocking",
                }
            ],
        },
        headers=h,
    )
    assert r.status_code == 201, r.text
    spec = r.json()
    assert len(spec["rules"]) == 1

    # batch zero
    r = await client.post(
        "/api/v1/multifiber-batches",
        json={
            "batch_code": "MF-1",
            "reference_lab_values": {"cotton": {"L": 96.0, "a": 0.1, "b": 0.9}},
        },
        headers=h,
    )
    assert r.status_code == 201, r.text

    # seeded test methods are visible
    r = await client.get("/api/v1/test-methods", headers=h)
    assert r.status_code == 200
    assert any(m["code"] == "ISO_105_X12" for m in r.json())

    # create job linked to the spec
    r = await client.post(
        "/api/v1/test-jobs",
        json={
            "brand_specification_id": spec["id"],
            "test_method_code": "ISO_105_X12",
            "article_code": "ART1",
            "lot_code": "LOT1",
        },
        headers=h,
    )
    assert r.status_code == 201, r.text
    job_id = r.json()["id"]

    # submit a FAILING manual result (delta_e 2.5 > 1.0)
    r = await client.post(
        f"/api/v1/test-jobs/{job_id}/manual-result",
        json={
            "test_method_code": "ISO_105_X12",
            "fibers": {"cotton": {"delta_e": 2.5, "gray_scale_grade": 3.0}},
        },
        headers=h,
    )
    assert r.status_code == 201, r.text
    assert r.json()["pass_fail"]["overall_pass"] is False

    # job is now failed, and the result is retrievable
    r = await client.get(f"/api/v1/test-jobs/{job_id}", headers=h)
    assert r.json()["status"] == "failed"
    r = await client.get(f"/api/v1/test-jobs/{job_id}/results", headers=h)
    assert len(r.json()) == 1
