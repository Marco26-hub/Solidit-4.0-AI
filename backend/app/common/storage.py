"""Object-storage abstraction. Local filesystem backend for dev; an
S3-compatible backend (signed URLs, encryption at rest) lands in Sprint 3/Phase 9.
Storage keys are always app-generated; we still guard against path traversal."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

from app.config import settings


class StorageBackend(Protocol):
    def put(self, key: str, data: bytes, content_type: str = ...) -> str: ...
    def get(self, key: str) -> bytes: ...
    def exists(self, key: str) -> bool: ...


class LocalStorage:
    def __init__(self, base_dir: str) -> None:
        self._base = Path(base_dir).resolve()

    def _path(self, key: str) -> Path:
        p = (self._base / key).resolve()
        if p != self._base and not str(p).startswith(str(self._base) + os.sep):
            raise ValueError("invalid storage key (path traversal)")
        return p

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()


_storage: LocalStorage | None = None


def get_storage() -> StorageBackend:
    global _storage
    if _storage is None:
        # TODO (Phase 9): return an S3Storage when settings.s3_endpoint_url is set.
        _storage = LocalStorage(settings.storage_local_dir)
    return _storage
