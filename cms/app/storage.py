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


def get_storage() -> Storage:
    kind = getattr(settings, "media_storage", "local")
    if kind == "local":
        return LocalStorage()
    # S3 storage added in a later step (feat/cms-imaging s3 backend)
    raise ValueError(f"Unknown MEDIA_STORAGE backend: {kind}")
