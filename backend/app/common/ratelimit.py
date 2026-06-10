"""Lightweight in-process sliding-window rate limiter for auth endpoints.

Single-process only (good enough for a single backend instance / demo). For
multi-instance production, back this with Redis (settings.redis_url) — same
interface. Used as a FastAPI dependency.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Request

from app.common.errors import AppError

_BUCKETS: dict[str, deque[float]] = defaultdict(deque)


class RateLimitedError(AppError):
    status_code = 429
    code = "rate_limited"


def rate_limit(
    limit: int, window_seconds: int, scope: str
) -> Callable[[Request], Coroutine[Any, Any, None]]:
    async def _dependency(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        key = f"{scope}:{ip}"
        now = time.monotonic()
        cutoff = now - window_seconds
        bucket = _BUCKETS[key]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            raise RateLimitedError("Too many requests; please slow down.")
        bucket.append(now)

    return _dependency


def reset() -> None:
    """Clear all buckets (used by tests)."""
    _BUCKETS.clear()
