"""Upload already-generated local renditions to S3.

Because the DB stores rendition file_path as a relative key
(e.g. renditions/790/thumbnail_400.webp) and the API computes URLs via the
storage backend, uploading the local media/ files to S3 at those same keys is
sufficient — no DB rewrite needed. After this, MEDIA_STORAGE=s3 serves S3 URLs.

Run from cms/:
    env -u PYTHONPATH uv run python upload_renditions_to_s3.py
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.db import engine
from app.models import Rendition
from app.storage import S3Storage


def main() -> None:
    storage = S3Storage()
    local_root = Path(settings.media_root)
    with Session(engine) as db:
        rows = db.query(Rendition).all()
        print(f"uploading {len(rows)} renditions to s3://{storage.bucket}")
        done = 0
        errors = 0
        for r in rows:
            rel = Path(r.file_path).as_posix()
            local_file = local_root / r.file_path.replace("\\", "/")
            if not local_file.is_file():
                errors += 1
                print(f"  MISSING local: {r.file_path}")
                continue
            data = local_file.read_bytes()
            # regenerate if zero-byte / stale
            try:
                storage.put(rel, data, content_type="image/webp")
                done += 1
            except Exception as e:  # noqa: BLE001
                errors += 1
                print(f"  UPLOAD ERR {r.file_path}: {e}")
            if done % 300 == 0:
                db.rollback()  # keep session fresh
        print("UPLOAD_DONE ok:", done, "| errors:", errors)


if __name__ == "__main__":
    main()
