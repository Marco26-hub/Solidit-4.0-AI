"""Alembic environment.

Migrations run through a SYNC psycopg2 engine (the runtime app uses async
asyncpg). asyncpg's prepared-statement protocol rejects multi-statement DDL
blocks, and psycopg2 happily runs them, so DDL stays readable. The migration
role is privileged and owns the objects; the app role is NON-superuser so RLS
applies at runtime.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

import app.db.models  # noqa: F401  (populate Base.metadata)
from app.config import settings
from app.db.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _sync_url() -> str:
    # app uses +asyncpg; migrations use sync +psycopg2
    return settings.migration_database_url.replace("+asyncpg", "+psycopg2")


def run_migrations_offline() -> None:
    context.configure(
        url=_sync_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_sync_url(), future=True)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
