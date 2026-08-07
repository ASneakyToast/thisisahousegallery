"""Generate renditions for all images and populate the renditions table.

Reads each original from the local backup dir (by the DB file_path), generates
the WebP rendition set via app.imaging, stores them through the Storage
abstraction, and inserts Rendition rows.

The originals live outside the repo (e.g. ~/housegallery-backup/media); only
code is committed.

Run from cms/:
    env -u PYTHONPATH uv run python generate_renditions.py \
        --src C:/Users/Joel/housegallery-backup/media
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from sqlalchemy.orm import Session

from app.db import engine
from app.imaging import generate_renditions, rendition_rel_path
from app.models import Image, Rendition
from app.storage import get_storage


def generate(src_root: Path) -> None:
    storage = get_storage()
    with Session(engine) as db:
        images = db.query(Image).all()
        print(f"processing {len(images)} images")
        done = 0
        failed = 0
        for img in images:
            src = src_root / img.file_path.replace("\\", "/")
            if not src.is_file():
                failed += 1
                print(f"  MISSING src: {img.file_path}")
                continue
            data = src.read_bytes()
            results = generate_renditions(data, storage)
            for r in results:
                if r.error:
                    failed += 1
                    print(f"  ERROR img {img.id} {r.key}: {r.error}")
                    continue
                rel = rendition_rel_path(img.id, r.key)
                url = storage.put(rel, r.data, content_type="image/webp")
                # upsert rendition row
                existing = db.query(Rendition).filter_by(
                    image_id=img.id, filter_spec=r.filter_spec
                ).first()
                if existing:
                    existing.file_path = rel
                    existing.width = r.width
                    existing.height = r.height
                    existing.file_size = len(r.data)
                else:
                    db.add(
                        Rendition(
                            image_id=img.id,
                            filter_spec=r.filter_spec,
                            file_path=rel,
                            width=r.width,
                            height=r.height,
                            file_size=len(r.data),
                        )
                    )
            done += 1
            if done % 100 == 0:
                db.commit()
                print(f"  ... {done}/{len(images)}")
        db.commit()
        print("RENDITION_DONE images processed:", done, "| issues:", failed)
        print("rendition rows:", db.query(Rendition).count())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True, help="path to media originals root")
    args = parser.parse_args()
    generate(Path(args.src))
