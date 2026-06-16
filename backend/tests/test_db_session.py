from __future__ import annotations

from app.db.session import _prepare_async_engine_config


def test_asyncpg_sslmode_require_maps_to_connect_args():
    url, connect_args = _prepare_async_engine_config(
        "postgresql+asyncpg://user:pass@example.test:5432/solidita"
        "?sslmode=require&application_name=solidita"
    )

    assert "sslmode" not in url
    assert "application_name=solidita" in url
    assert connect_args == {"ssl": True}


def test_asyncpg_sslmode_disable_maps_to_connect_args():
    url, connect_args = _prepare_async_engine_config(
        "postgresql+asyncpg://user:pass@example.test:5432/solidita?sslmode=disable"
    )

    assert "sslmode" not in url
    assert connect_args == {"ssl": False}


def test_psycopg_sslmode_stays_in_url():
    url, connect_args = _prepare_async_engine_config(
        "postgresql+psycopg2://user:pass@example.test:5432/solidita?sslmode=require"
    )

    assert "sslmode=require" in url
    assert connect_args == {}
