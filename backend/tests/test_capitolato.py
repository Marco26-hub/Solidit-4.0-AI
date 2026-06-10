from __future__ import annotations

import uuid

import pytest

from app.brand_specs.service import parse_rules_csv
from app.common.errors import AppError


# ── pure CSV parser (no DB) ─────────────────────────────────────────────────────
def test_parse_csv_italian_semicolon_and_decimal_comma():
    csv_text = (
        "metodo;fibra;max_de;min_grey;severita\n"
        "ISO_105_X12;cotton;1,0;4,0;blocking\n"
        "ISO_105_C06;;0,8;;warning\n"
    )
    rules = parse_rules_csv(csv_text)
    assert len(rules) == 2
    assert rules[0].test_method_code == "ISO_105_X12"
    assert rules[0].max_delta_e == 1.0
    assert rules[0].min_gray_scale_grade == 4.0
    assert rules[0].severity == "blocking"
    assert rules[1].fiber_code is None
    assert rules[1].max_delta_e == 0.8
    assert rules[1].min_gray_scale_grade is None
    assert rules[1].severity == "warning"


def test_parse_csv_comma_delimiter_no_header():
    rules = parse_rules_csv("ISO_105_X12,cotton,1.0,4.0,blocking")
    assert len(rules) == 1
    assert rules[0].test_method_code == "ISO_105_X12"


def test_parse_csv_bad_number_raises():
    with pytest.raises(AppError):
        parse_rules_csv("ISO_105_X12,cotton,abc,4.0,blocking")


def test_parse_csv_empty_raises():
    with pytest.raises(AppError):
        parse_rules_csv("   ")


# ── import + document attach (DB) ───────────────────────────────────────────────
async def _register(client, email, company):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "company_name": company},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_import_capitolato_csv(client, require_db):
    reg = await _register(client, f"cap-{uuid.uuid4().hex[:8]}@example.com", "Cap Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}
    csv_text = "ISO_105_X12,cotton,1.0,4.0,blocking\nISO_105_C06,,0.8,,warning"
    r = await client.post(
        "/api/v1/brand-specifications/import",
        json={"brand_name": "Zara", "rules_csv": csv_text},
        headers=h,
    )
    assert r.status_code == 201, r.text
    spec = r.json()
    assert spec["brand_name"] == "Zara"
    assert len(spec["rules"]) == 2


async def test_attach_and_download_capitolato_document(client, require_db):
    reg = await _register(client, f"doc-{uuid.uuid4().hex[:8]}@example.com", "Doc Co")
    h = {"Authorization": f"Bearer {reg['access_token']}"}
    spec = (
        await client.post(
            "/api/v1/brand-specifications",
            json={"brand_name": "Zara", "rules": []},
            headers=h,
        )
    ).json()

    pdf = b"%PDF-1.4 capitolato test"
    r = await client.post(
        f"/api/v1/brand-specifications/{spec['id']}/document",
        files={"file": ("capitolato.pdf", pdf, "application/pdf")},
        headers=h,
    )
    assert r.status_code == 200, r.text
    doc = r.json()["metadata"]["capitolato_document"]
    assert doc["filename"] == "capitolato.pdf"
    assert len(doc["sha256"]) == 64

    r = await client.get(f"/api/v1/brand-specifications/{spec['id']}/document", headers=h)
    assert r.status_code == 200
    assert r.content == pdf
