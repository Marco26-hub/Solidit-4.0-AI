"""Insert a demo company + admin user. Idempotent-ish: skips if email exists.

Run: python -m app.scripts.seed   (needs a migrated database reachable)
"""

from __future__ import annotations

import asyncio

from app.auth.service import register
from app.common.errors import ConflictError


async def main() -> None:
    try:
        resp = await register(
            email="admin@example.com",
            password="changeme123",
            full_name="Demo Admin",
            company_name="Tintoria Demo",
            vat_number="IT00000000000",
        )
        print(f"Seeded demo company {resp.company_id} (login: admin@example.com / changeme123)")
    except ConflictError:
        print("Demo user already exists — nothing to do.")


if __name__ == "__main__":
    asyncio.run(main())
