"""configurable multifiber strip profiles + batch link

Revision ID: 0004_strip_profiles
Revises: 0003_refresh_tokens
Create Date: 2026-06-09

Multifiber strips differ by standard (AATCC vs ISO / UNI EN ISO 105-F10 DW/TV):
different fibre types, order and composition. Seed common profiles (editable by
the lab — these are reference compositions to VERIFY against the physical strip,
not protected grading equations).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0004_strip_profiles"
down_revision: str | None = "0003_refresh_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# code, name, standard_family, ordered fibre codes
PROFILES = [
    (
        "AATCC_MULTIFIBER_10",
        "AATCC Multifiber No. 10",
        "AATCC",
        ["acetate", "cotton", "nylon", "polyester", "acrylic", "wool"],
    ),
    (
        "AATCC_MULTIFIBER_1",
        "AATCC Multifiber No. 1",
        "AATCC",
        ["acetate", "cotton", "nylon", "silk", "viscose", "wool"],
    ),
    (
        "ISO_105_F10_DW",
        "ISO / UNI EN ISO 105-F10 multifibre DW",
        "ISO 105-F10",
        ["diacetate", "cotton", "polyamide", "polyester", "acrylic", "wool"],
    ),
    (
        "ISO_105_F10_TV",
        "ISO / UNI EN ISO 105-F10 multifibre TV",
        "ISO 105-F10",
        ["triacetate", "cotton", "polyamide", "polyester", "acrylic", "viscose"],
    ),
]


def upgrade() -> None:
    op.execute("ALTER TABLE multifiber_batches ADD COLUMN strip_profile_code TEXT;")
    op.execute(
        """
        CREATE TABLE multifiber_strip_profiles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            standard_family TEXT,
            fibers JSONB NOT NULL,
            is_builtin BOOLEAN NOT NULL DEFAULT TRUE
        );
        """
    )
    for code, name, family, fibers in PROFILES:
        fibers_json = "[" + ", ".join(f"'{f}'" for f in fibers) + "]"
        op.execute(
            "INSERT INTO multifiber_strip_profiles (code, name, standard_family, fibers) "
            f"VALUES ('{code}', '{name}', '{family}', "
            f"CAST('{fibers_json.replace(chr(39), chr(34))}' AS jsonb)) "
            "ON CONFLICT (code) DO NOTHING;"
        )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'solidita_app') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON multifiber_strip_profiles TO solidita_app;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS multifiber_strip_profiles;")
    op.execute("ALTER TABLE multifiber_batches DROP COLUMN IF EXISTS strip_profile_code;")
