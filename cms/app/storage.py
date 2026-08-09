"""Storage abstraction for image files and renditions.

The CMS stores two kinds of artifacts:
  - original full-res files
  - generated renditions (multiple sizes)

This module defines a simple `Storage` interface so the backend (local disk
now, S3 later) can be swapped without changing the imaging pipeline. The
concrete backend is chosen by the `MEDIA_STORAGE` setting ("local" for now;
"dummy" for tests).

URLs are absolute so a future origin swap is a config change, not a rewrite.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urljoin

from app.config import settings


class Storage:
    """Base storage interface."""

    def put(self, rel_path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Store bytes at rel_path, return its public URL."""
        raise NotImplementedError

    def url(self, rel_path: str) -> str:
        """Return the public URL for an existing stored object."""
        raise NotImplementedError

    def exists(self, rel_path: str) -> bool:
        raise NotImplementedError


class LocalStorage(Storage):
    """Stores files under MEDIA_ROOT on local disk, served via /media statically."""

    def __init__(self, root: str | Path | None = None, public_base: str | None = None):
        self.root = Path(root or settings.media_root)
        self.public_base = public_base or settings.media_url
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, rel_path: str) -> Path:
        # guard against path traversal
        safe = Path(rel_path).as_posix().lstrip("/")
        return (self.root / safe).resolve()

    def put(self, rel_path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        dest = self._path(rel_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return self.url(rel_path)

    def url(self, rel_path: str) -> str:
        return urljoin(self.public_base, Path(rel_path).as_posix())

    def exists(self, rel_path: str) -> bool:
        return self._path(rel_path).is_file()


class S3Storage(Storage):
    """Stores files in an AWS S3 bucket. Serves public URLs via the bucket.

    Uses the CMS app's scoped IAM credentials (aws_access_key_id /
    aws_secret_access_key from settings / .env).
    """

    def __init__(self, bucket: str | None = None, region: str | None = None):
        import boto3  # local import keeps boto3 optional for local usage

        self.bucket = bucket or settings.aws_s3_bucket
        self.region = region or settings.aws_region
        self.client = boto3.client(
            "s3",
            region_name=self.region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )
        # Public URL base: either explicit, or virtual-hosted-style bucket URL
        self._public_base = settings.s3_base_url or (
            f"https://{self.bucket}.s3.{self.region}.amazonaws.com"
        )

    def put(self, rel_path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        safe = Path(rel_path).as_posix().lstrip("/")
        self.client.put_object(
            Bucket=self.bucket,
            Key=safe,
            Body=data,
            ContentType=content_type,
        )
        return self.url(rel_path)

    def url(self, rel_path: str) -> str:
        return urljoin(self._public_base + "/", Path(rel_path).as_posix())

    def exists(self, rel_path: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=Path(rel_path).as_posix().lstrip("/"))
            return True
        except Exception:
            return False


def get_storage() -> Storage:
    kind = getattr(settings, "media_storage", "local")
    if kind == "local":
        return LocalStorage()
    if kind == "s3":
        return S3Storage()
    raise ValueError(f"Unknown MEDIA_STORAGE backend: {kind}")
