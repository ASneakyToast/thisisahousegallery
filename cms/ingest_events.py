"""Backfill events (schedule) from the Wagtail dump into the CMS.

The main ingest now imports exhibitions_eventpage on fresh installs, but existing
DBs already have exhibitions/artists/images loaded. This script additively inserts
just the events (3 in the source) into the Event model, matching:
  - title/slug from wagtailcore_page (via page_ptr_id)
  - related_exhibition by source id -> existing Exhibition (by title)
  - featured_image by source file_path -> existing Image
Idempotent: skips events whose slug already exists.

Run from cms/:
    env -u PYTHONPATH uv run python ingest_events.py <path-to-dump.sql>
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.db import engine
from app.models import Event, Exhibition, Image

_COPY_RE = re.compile(r"^COPY public\.([a-z_]+) \(([^)]*)\) FROM stdin;$")
WANTED = {"exhibitions_eventpage", "exhibitions_exhibitionpage", "wagtailcore_page", "images_customimage"}


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
            if cur not in WANTED:
                continue
            vals = _split(line)
            if len(vals) == len(cols):
                data[cur].append(dict(zip(cols, vals)))
    return dict(data)


def _int_or_none(v):
    if v is None or v == "":
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _parse_date(v):
    if not v:
        return None
    try:
        return datetime.fromisoformat(str(v).replace(" ", "T"))
    except ValueError:
        return None


def _parse_time(v):
    if not v:
        return None
    from datetime import time as dtime
    try:
        return datetime.combine(datetime(2020, 1, 1), dtime.fromisoformat(str(v)))
    except ValueError:
        return None


def _bool(v):
    return v in (True, "t", "true", "1", 1)


def _slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "untitled"


def backfill(path: Path) -> None:
    data = _parse(path)
    page_title = {p["id"]: (p.get("title") or "") for p in data.get("wagtailcore_page", [])}
    src_img_path = {im["id"]: (im.get("file") or "") for im in data.get("images_customimage", [])}
    # Source exhibition page_ptr_id -> its title (from the same page table the
    # main ingest used), so we can link events to existing CMS exhibitions by title.
    src_exh_page_title = {
        ex["page_ptr_id"]: (page_title.get(ex["page_ptr_id"]) or "").strip().lower()
        for ex in data.get("exhibitions_exhibitionpage", [])
    }

    with Session(engine) as db:
        exhs = {e.title.strip().lower(): e for e in db.query(Exhibition).all()}
        imgs = {i.file_path: i.id for i in db.query(Image).all()}
        existing_slugs = {e.slug for e in db.query(Event).all()}

        added = skipped = 0
        for ev in data.get("exhibitions_eventpage", []):
            title = page_title.get(ev["page_ptr_id"], "")
            if not title:
                skipped += 1
                continue
            slug = ev.get("slug") or _slugify(title)
            if slug in existing_slugs:
                skipped += 1
                continue
            # related_exhibition_id in the dump is a source exhibition page id;
            # resolve it to the existing CMS exhibition by matching its title.
            rel_exh_source = ev.get("related_exhibition_id")
            rel_exh_cms = None
            if rel_exh_source:
                rel_title = src_exh_page_title.get(rel_exh_source)
                if rel_title:
                    rel_exh_cms = exhs.get(rel_title)  # id resolved via relationship below
            feat_img = ev.get("featured_image_id")
            img_path = src_img_path.get(feat_img) if feat_img else ""
            feat_img_id = imgs.get(img_path) if img_path else None
            db.add(Event(
                title=title,
                slug=slug,
                event_type=ev.get("event_type") or "",
                tagline=ev.get("tagline") or "",
                related_exhibition_id=rel_exh_cms.id if rel_exh_cms else None,
                start_date=_parse_date(ev.get("start_date")),
                end_date=_parse_date(ev.get("end_date")),
                start_time=_parse_time(ev.get("start_time")),
                end_time=_parse_time(ev.get("end_time")),
                all_day=_bool(ev.get("all_day")),
                custom_venue_name=ev.get("custom_venue_name") or "",
                custom_address=ev.get("custom_address") or "",
                location_details=ev.get("location_details") or "",
                description=ev.get("description") or "",
                capacity=_int_or_none(ev.get("capacity")),
                registration_required=_bool(ev.get("registration_required")),
                registration_link=ev.get("registration_link") or "",
                ticket_price=ev.get("ticket_price") or "",
                contact_email=ev.get("contact_email") or "",
                external_link=ev.get("external_link") or "",
                featured_on_schedule=_bool(ev.get("featured_on_schedule")),
                featured_image_id=feat_img_id,
            ))
            existing_slugs.add(slug)
            added += 1
        db.commit()
        print("EVENT_INGEST_OK")
        print(f"  added   : {added}")
        print(f"  skipped : {skipped}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python ingest_events.py <path-to-dump.sql>")
        sys.exit(1)
    backfill(Path(sys.argv[1]))