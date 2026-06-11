"""Object-storage abstraction. Local filesystem backend for dev; an
S3-compatible backend for production (works with AWS S3, Cloudflare R2, MinIO,
Backblaze B2, etc.). Storage keys are always app-generated; we still guard
against path traversal on the local backend.

Production selection is by config: when ``s3_bucket`` + credentials are present
(``s3_access_key`` / ``s3_secret_key``, optionally ``s3_endpoint_url`` for an
S3-compatible provider), ``get_storage()`` returns an ``S3Storage``. Otherwise it
falls back to ``LocalStorage`` (dev only — NOT suitable for serverless/multi-instance)."""

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


class S3Storage:
    """S3-compatible object storage. boto3 is imported lazily so the base app
    installs without it (install with the ``storage`` extra)."""

    def __init__(
        self,
        bucket: str,
        *,
        endpoint_url: str | None,
        region: str,
        access_key: str | None,
        secret_key: str | None,
    ) -> None:
        import boto3

        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            # encryption at rest (server-side); providers without SSE ignore it
            ServerSideEncryption="AES256",
        )
        return key

    def get(self, key: str) -> bytes:
        obj = self._client.get_object(Bucket=self._bucket, Key=key)
        return obj["Body"].read()

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError:
            return False


_storage: StorageBackend | None = None


def get_storage() -> StorageBackend:
    global _storage
    if _storage is None:
        if settings.s3_access_key and settings.s3_secret_key:
            _storage = S3Storage(
                settings.s3_bucket,
                endpoint_url=settings.s3_endpoint_url,
                region=settings.s3_region,
                access_key=settings.s3_access_key,
                secret_key=settings.s3_secret_key,
            )
        else:
            _storage = LocalStorage(settings.storage_local_dir)
    return _storage
