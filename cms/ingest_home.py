"""Backfill the HomePage (hero) content from the Wagtail home_homepage dump.

Parses home_homepage.body StreamField JSON, extracts the hero block's intro +
ordered floating_images image ids, and (re)creates a single HomePage row.
Idempotent: upserts the first HomePage row.

Run from cms/:
    env -u PYTHONPATH uv run python ingest_home.py <path-to-dump.sql>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from app.db import engine
from app.models import HomePage, Image, Site

_COPY_RE = re.compile(r"^COPY public\.home_homepage \(([^)]*)\) FROM stdin;$")
_IMG_COPY_RE = re.compile(r"^COPY public\.images_customimage \(([^)]*)\) FROM stdin;$")


def _split(row: str) -> list:
    """Split one COPY data row, matching the escaping proven in ingest_from_dump."""
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
    data: dict[str, list[dict]] = {"home_homepage": [], "images_customimage": []}
    cur, cols = None, []
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\r\n")
            m = _COPY_RE.match(line)
            if m:
                cur = "home_homepage"
                cols = [c.strip() for c in m.group(1).split(",")]
                continue
            m2 = _IMG_COPY_RE.match(line)
            if m2:
                cur = "images_customimage"
                cols = [c.strip() for c in m2.group(1).split(",")]
                continue
            if cur is None:
                continue
            if line.startswith("\\."):
                cur = None
                continue
            vals = _split(line)
            if len(vals) == len(cols):
                data[cur].append(dict(zip(cols, vals)))
    return data


def _extract_hero(body_str):
    """Return (intro, floating_image_ids) from the 'hero' block, if present."""
    try:
        if isinstance(body_str, str):
            # The dump stores rich-text quotes doubly-escaped (\\\"); collapse
            # \\ -> \ so the result is valid JSON before parsing.
            body_str = body_str.replace("\\\\", "\\")
            body = json.loads(body_str)
        else:
            body = body_str or []
    except Exception:
        return "", []
    for block in body if isinstance(body, list) else []:
        if isinstance(block, dict) and block.get("type") == "hero":
            val = block.get("value") or {}
            intro = val.get("intro") or ""
            fids = []
            for item in val.get("floating_images") or []:
                if isinstance(item, dict) and item.get("value") not in (None, ""):
                    try:
                        fids.append(int(item["value"]))
                    except (TypeError, ValueError):
                        continue
            return intro, fids
    return "", []


def backfill(path: Path) -> None:
    data = _parse(path)
    rows = data.get("home_homepage", [])
    # Source image id -> file_path, then -> CMS Image id (by file_path).
    src_img_path = {
        im["id"]: (im.get("file") or "") for im in data.get("images_customimage", [])
    }
    with Session(engine) as db:
        site = db.query(Site).order_by(Site.id).first()
        site_id = site.id if site else None
        cms_by_path = {i.file_path: i.id for i in db.query(Image).all()}
        found = 0
        for row in rows:
            body = row.get("body")
            if not body:
                continue
            intro, fids_src = _extract_hero(body)
            found += 1
            # Resolve source image ids -> CMS image ids by file_path.
            fids = []
            for src_id in fids_src:
                fp = src_img_path.get(str(src_id))
                cms_id = cms_by_path.get(fp) if fp else None
                if cms_id:
                    fids.append(cms_id)
            hp = db.query(HomePage).order_by(HomePage.id).first()
            if hp:
                hp.intro = intro
                hp.floating_image_ids = fids
                hp.site_id = site_id
            else:
                db.add(HomePage(intro=intro, floating_image_ids=fids, site_id=site_id))
            break  # single homepage
        db.commit()
        hp = db.query(HomePage).order_by(HomePage.id).first()
        print("HOME_INGEST_OK")
        print(f"  homepage row parsed : {found}")
        if hp:
            print(f"  intro               : {hp.intro[:80]!r}...")
            print(f"  cms floating ids    : {hp.floating_image_ids}")
            print(f"  count               : {len(hp.floating_image_ids)}")
        else:
            print("  NO HOMEPAGE FOUND")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python ingest_home.py <path-to-dump.sql>")
        sys.exit(1)
    backfill(Path(sys.argv[1]))