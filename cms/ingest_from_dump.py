"""Ingest content from the Wagtail Postgres dump into the CMS.

Reads a pg_dump (COPY format) produced from the Wagtail site, transforms the
entities we care about into the clean CMS schema, and inserts them.

The dump is a plain-text SQL file (e.g. fresh-20260803-2056.sql). This is a
transform, not a copy: Wagtail's page-based model maps onto our flat models.

The dump file itself is NOT committed (it lives outside the repo, e.g.
~/housegallery-backup/db/). This script only reads from it by path.

Run from cms/:
    env -u PYTHONPATH uv run python ingest_from_dump.py <path-to-dump.sql>
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.db import engine
from app.models import (
    Artist,
    Artwork,
    ArtworkArtist,
    ArtworkImage,
    ArtworkTag,
    Event,
    Exhibition,
    ExhibitionArtist,
    ExhibitionArtwork,
    Image,
    Site,
    SiteSettings,
    Tag,
)

# ---------------------------------------------------------------------------
# Minimal COPY-format parser
# ---------------------------------------------------------------------------

_COPY_RE = re.compile(r"^COPY public\.([a-z_]+) \(([^)]*)\) FROM stdin;$")

REQUIRED_TABLES = [
    "artists_artist",
    "artworks_artwork",
    "artworks_artworkartist",
    "artworks_artworkimage",
    "artworks_artworktag",
    "exhibitions_exhibitionpage",
    "exhibitions_exhibitionartist",
    "exhibitions_exhibitionartwork",
    "exhibitions_eventpage",
    "images_customimage",
    "taggit_tag",
    "wagtailcore_page",
]


def split_copy_row(line: str) -> list:
    """Split one COPY data row into fields.

    PostgreSQL COPY: fields are tab-separated; the NULL marker is the two
    chars '\\N'; a quoted field is wrapped in double-quotes and may contain
    escaped characters. Tabs cannot appear inside an unquoted field.
    """
    out = []
    for f in line.split("\t"):
        if f == "\\N":
            out.append(None)
            continue
        if len(f) >= 2 and f.startswith('"') and f.endswith('"'):
            inner = f[1:-1]
            inner = inner.replace("\\\\", "\x00").replace('\\"', '"').replace(
                "\x00", "\\"
            )
            out.append(inner)
        else:
            out.append(f)
    return out


def parse_copy(path: Path) -> dict[str, list[dict]]:
    data: defaultdict[str, list[dict]] = defaultdict(list)
    cur_table = None
    cur_columns: list[str] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\r\n")
            m = _COPY_RE.match(line)
            if m:
                cur_table = m.group(1)
                cur_columns = [c.strip() for c in m.group(2).split(",")]
                continue
            if cur_table is None:
                continue
            if line.startswith("\\."):
                cur_table = None
                continue
            if cur_table not in REQUIRED_TABLES:
                continue
            values = split_copy_row(line)
            if len(values) != len(cur_columns):
                continue
            data[cur_table].append(dict(zip(cur_columns, values)))
    return dict(data)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ARTWORK_SLUGS: set[str] = set()


def _slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "untitled"


def _artwork_slug(title: str, raw_id: str) -> str:
    base = _slugify(title)
    slug = base
    n = 2
    while slug in _ARTWORK_SLUGS:
        slug = f"{base}-{n}"
        n += 1
    _ARTWORK_SLUGS.add(slug)
    return f"{slug}-{raw_id}"[:200]


def _parse_date(v):
    if not v:
        return None
    try:
        return datetime.fromisoformat(str(v).replace(" ", "T"))
    except ValueError:
        return None


def _parse_time(v):
    """Parse an HH:MM:SS time into a datetime (date part ignored)."""
    if not v:
        return None
    from datetime import time as dtime
    try:
        return datetime.combine(datetime(2020, 1, 1), dtime.fromisoformat(str(v)))
    except ValueError:
        return None


def _bool(v):
    if v in (True, "t", "true", "1", 1):
        return True
    if v in (False, "f", "false", "0", 0, None, "\\N"):
        return False
    return False


def _float(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _int_or_none(v):
    if v is None or v == "":
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _json_or_list(v):
    if not v or v == "[]":
        return []
    try:
        parsed = json.loads(v)
        return parsed if isinstance(parsed, list) else [parsed]
    except (TypeError, ValueError):
        return []


# ---------------------------------------------------------------------------
# Transform + load
# ---------------------------------------------------------------------------

def ingest(path: Path) -> None:
    data = parse_copy(path)

    artists_src = data.get("artists_artist", [])
    artworks_src = data.get("artworks_artwork", [])
    images_src = data.get("images_customimage", [])
    tags_src = data.get("taggit_tag", [])
    exhibitions_src = data.get("exhibitions_exhibitionpage", [])
    pages_src = {p["id"]: p for p in data.get("wagtailcore_page", [])}

    with Session(engine) as db:
        site = db.query(Site).filter_by(slug="thisisahousegallery").first()
        if site is None:
            site = Site(slug="thisisahousegallery", name="This is a House Gallery")
            db.add(site)
            db.flush()
            db.add(
                SiteSettings(
                    site_id=site.id,
                    site_title="This is a House Gallery",
                )
            )

        # Tags
        tag_id_map: dict[str, int] = {}
        for t in tags_src:
            tag = Tag(name=t["name"], slug=t["slug"], tenant_id=site.id)
            db.add(tag)
            db.flush()
            tag_id_map[t["id"]] = tag.id

        # Images
        image_id_map: dict[str, int] = {}
        for im in images_src:
            img = Image(
                title=im.get("title") or "",
                alt=im.get("alt") or "",
                credit=im.get("credit") or "",
                description=im.get("description") or "",
                file_path=im.get("file") or "",
                width=_int_or_none(im.get("width")) or 0,
                height=_int_or_none(im.get("height")) or 0,
                file_size=_int_or_none(im.get("file_size")) or 0,
                tenant_id=site.id,
            )
            db.add(img)
            db.flush()
            image_id_map[im["id"]] = img.id

        # Artists
        used_artist_slugs: set[str] = set()
        artist_id_map: dict[str, int] = {}
        for a in artists_src:
            base_slug = _slugify(a["name"])
            slug = base_slug
            n = 2
            while slug in used_artist_slugs:
                slug = f"{base_slug}-{n}"
                n += 1
            used_artist_slugs.add(slug)
            profile = a.get("profile_image_id")
            artist = Artist(
                name=a["name"],
                slug=slug,
                bio=a.get("bio") or "",
                website=a.get("website") or "",
                email=a.get("email") or "",
                birth_year=_int_or_none(a.get("birth_year")),
                socials=_json_or_list(a.get("social_media_links")),
                profile_image_id=image_id_map.get(profile) if profile else None,
                tenant_id=site.id,
            )
            db.add(artist)
            db.flush()
            artist_id_map[a["id"]] = artist.id

        # Artworks
        artwork_id_map: dict[str, int] = {}
        for aw in artworks_src:
            artwork = Artwork(
                title=aw.get("title") or "",
                slug=_artwork_slug(aw.get("title") or "", aw["id"]),
                description=aw.get("description") or "",
                size=aw.get("size") or "",
                width_inches=_float(aw.get("width_inches")),
                height_inches=_float(aw.get("height_inches")),
                depth_inches=_float(aw.get("depth_inches")),
                date=_parse_date(aw.get("date")),
                price=aw.get("price") or "",
                artifacts=_json_or_list(aw.get("artifacts")),
                tenant_id=site.id,
            )
            db.add(artwork)
            db.flush()
            artwork_id_map[aw["id"]] = artwork.id

        # Artwork relationships
        for rel in data.get("artworks_artworkartist", []):
            if rel.get("artwork_id") in artwork_id_map and rel.get("artist_id") in artist_id_map:
                db.add(
                    ArtworkArtist(
                        artwork_id=artwork_id_map[rel["artwork_id"]],
                        artist_id=artist_id_map[rel["artist_id"]],
                        sort_order=_int_or_none(rel.get("sort_order")) or 0,
                    )
                )
        for rel in data.get("artworks_artworkimage", []):
            if rel.get("artwork_id") in artwork_id_map and rel.get("image_id") in image_id_map:
                db.add(
                    ArtworkImage(
                        artwork_id=artwork_id_map[rel["artwork_id"]],
                        image_id=image_id_map[rel["image_id"]],
                        caption=rel.get("caption") or "",
                        sort_order=_int_or_none(rel.get("sort_order")) or 0,
                    )
                )
        for rel in data.get("artworks_artworktag", []):
            aw_id = rel.get("content_object_id") or rel.get("artwork_id")
            if aw_id in artwork_id_map and rel.get("tag_id") in tag_id_map:
                db.add(
                    ArtworkTag(
                        artwork_id=artwork_id_map[aw_id],
                        tag_id=tag_id_map[rel["tag_id"]],
                    )
                )

        # Exhibitions (title/slug from wagtailcore_page via page_ptr_id)
        exhibition_id_map: dict[str, int] = {}
        for ex in exhibitions_src:
            page = pages_src.get(ex["page_ptr_id"], {})
            if not page.get("title"):
                continue
            exhibition = Exhibition(
                title=page.get("title") or "",
                slug=page.get("slug") or _slugify(page.get("title") or ""),
                start_date=_parse_date(ex.get("start_date")),
                end_date=_parse_date(ex.get("end_date")),
                description=ex.get("description") or "",
                body=_json_or_list(ex.get("body")),
                video_embed_url=ex.get("video_embed_url") or "",
                listing_title=ex.get("listing_title") or "",
                listing_summary=ex.get("listing_summary") or "",
                listing_image_id=image_id_map.get(ex.get("listing_image_id"))
                if ex.get("listing_image_id")
                else None,
                tenant_id=site.id,
            )
            db.add(exhibition)
            db.flush()
            exhibition_id_map[ex["page_ptr_id"]] = exhibition.id

        # Exhibition relationships
        for rel in data.get("exhibitions_exhibitionartist", []):
            if rel.get("page_id") in exhibition_id_map and rel.get("artist_id") in artist_id_map:
                db.add(
                    ExhibitionArtist(
                        exhibition_id=exhibition_id_map[rel["page_id"]],
                        artist_id=artist_id_map[rel["artist_id"]],
                        sort_order=_int_or_none(rel.get("sort_order")) or 0,
                    )
                )
        for rel in data.get("exhibitions_exhibitionartwork", []):
            if rel.get("page_id") in exhibition_id_map and rel.get("artwork_id") in artwork_id_map:
                db.add(
                    ExhibitionArtwork(
                        exhibition_id=exhibition_id_map[rel["page_id"]],
                        artwork_id=artwork_id_map[rel["artwork_id"]],
                        sort_order=_int_or_none(rel.get("sort_order")) or 0,
                    )
                )

        # Events (title/slug from wagtailcore_page via page_ptr_id)
        event_id_map: dict[str, int] = {}
        for ev in data.get("exhibitions_eventpage", []):
            page = pages_src.get(ev["page_ptr_id"], {})
            if not page.get("title"):
                continue
            rel_exh = ev.get("related_exhibition_id")
            feat_img = ev.get("featured_image_id")
            event = Event(
                title=page.get("title") or "",
                slug=page.get("slug") or _slugify(page.get("title") or ""),
                event_type=ev.get("event_type") or "",
                tagline=ev.get("tagline") or "",
                related_exhibition_id=exhibition_id_map.get(rel_exh) if rel_exh else None,
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
                featured_image_id=image_id_map.get(feat_img) if feat_img else None,
                tenant_id=site.id,
            )
            db.add(event)
            db.flush()
            event_id_map[ev["page_ptr_id"]] = event.id

        db.commit()
        print("INGEST_OK site=", site.slug)
        print(f"  artists      : {len(artist_id_map)}")
        print(f"  artworks     : {len(artwork_id_map)}")
        print(f"  exhibitions  : {len(exhibition_id_map)}")
        print(f"  events       : {len(event_id_map)}")
        print(f"  images       : {len(image_id_map)}")
        print(f"  tags         : {len(tag_id_map)}")
