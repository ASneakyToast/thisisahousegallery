"""Backfill exhibition photos (showcards / installation / opening reception) from the Wagtail dump.

The main ingest (ingest_from_dump.py) imported exhibitions, artists, artworks and
images but did NOT import the exhibition *photo* tables — so the CMS had no
showcards, installation galleries, or opening-reception galleries. This script
additively backfills them into the ExhibitionPhoto model.

Safe to run against an already-loaded CMS DB:
- Matches each exhibition by the source page title -> CMS Exhibition.title
- Matches each image by S3 file_path -> CMS Image.file_path
- Skips a photo if its row already exists (idempotent; never duplicates)

Categories (source table -> ExhibitionPhoto.category):
  exhibitions_showcardphoto        -> "showcard"
  exhibitions_installationphoto    -> "installation"
  exhibitions_openingreceptionphoto-> "opening_reception"

Run from cms/:
    env -u PYTHONPATH uv run python ingest_exhibition_photos.py <path-to-dump.sql>
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

from sqlalchemy.orm import Session

from app.db import engine
from app.models import Exhibition, ExhibitionPhoto, Image

_COPY_RE = re.compile(r"^COPY public\.([a-z_]+) \(([^)]*)\) FROM stdin;$")

SOURCE_TABLES = {
    "exhibitions_showcardphoto": "showcard",
    "exhibitions_installationphoto": "installation",
    "exhibitions_openingreceptionphoto": "opening_reception",
}


def _split(row: str) -> list:
    out = []
    for f in row.split("\t"):
        if f == "\\N":
            out.append(None)
            continue
        if len(f) >= 2 and f.startswith('"') and f.endswith('"'):
            inner = f[1:-1]
            out.append(inner.replace("\\\\", "\x00").replace('\\"', '"').replace("\x00", "\\"))
        else:
            out.append(f)
    return out


def _parse(path: Path) -> dict[str, list[dict]]:
    data: defaultdict[str, list[dict]] = defaultdict(list)
    wanted = set(SOURCE_TABLES) | {"wagtailcore_page", "images_customimage"}
    cur, cols = None, []
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\r\n")
            m = _COPY_RE.match(line)
            if m:
                cur = m.group(1)
                cols = [c.strip() for c in m.group(2).split(",")]
                continue
            if cur is None:
                continue
            if line.startswith("\\."):
                cur = None
                continue
            if cur not in wanted:
                continue
            vals = _split(line)
            if len(vals) == len(cols):
                data[cur].append(dict(zip(cols, vals)))
    return dict(data)


def _int_or_none(v):
    if v is None or v == "":
        return 0
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def backfill(path: Path) -> None:
    data = _parse(path)

    # Build page_id -> title map from wagtailcore_page (id) — the photo tables
    # reference ExhibitionPage id via page_id.
    page_title = {
        p["id"]: (p.get("title") or "").strip()
        for p in data.get("wagtailcore_page", [])
        if p.get("title")
    }

    with Session(engine) as db:
        exhs = {e.title.strip().lower(): e for e in db.query(Exhibition).all()}
        # CMS images keyed by S3 file_path -> cms id
        imgs = {i.file_path: i.id for i in db.query(Image).all()}
        # source image id -> S3 file_path
        src_img_path = {
            im["id"]: (im.get("file") or "")
            for im in data.get("images_customimage", [])
        }
        existing = {
            (p.exhibition_id, p.image_id)
            for p in db.query(ExhibitionPhoto).all()
        }

        added = 0
        skipped = {"orphan_exh": 0, "orphan_img": 0, "dup": 0}

        for table, category in SOURCE_TABLES.items():
            for row in data.get(table, []):
                page_id = row.get("page_id")
                title = page_title.get(page_id)
                if not title:
                    skipped["orphan_exh"] += 1
                    continue
                ex = exhs.get(title.strip().lower())
                if ex is None:
                    skipped["orphan_exh"] += 1
                    continue
                src_id = row.get("image_id")
                img_path = src_img_path.get(src_id) if src_id else ""
                img_id = imgs.get(img_path) if img_path else None
                if img_id is None:
                    skipped["orphan_img"] += 1
                    continue
                if (ex.id, img_id) in existing:
                    skipped["dup"] += 1
                    continue
                db.add(
                    ExhibitionPhoto(
                        exhibition_id=ex.id,
                        image_id=img_id,
                        category=category,
                        sort_order=_int_or_none(row.get("sort_order")) or 0,
                    )
                )
                existing.add((ex.id, img_id))
                added += 1
        db.commit()

        print("PHOTO_INGEST_OK")
        print(f"  added            : {added}")
        for k, v in skipped.items():
            print(f"  skipped {k:12}: {v}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python ingest_exhibition_photos.py <path-to-dump.sql>")
        sys.exit(1)
    backfill(Path(sys.argv[1]))