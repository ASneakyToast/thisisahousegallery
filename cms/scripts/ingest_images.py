#!/usr/bin/env python
"""Ingest images: process, store, and create DB records.

Reuses the CMS imaging pipeline (app.imaging), storage abstraction
(app.storage), and ORM models (app.models) — no HTTP API dependency.

Usage:
    cd cms/

    # Phase 1: Ingest — process images and create DB records
    uv run python -m scripts.ingest_images ingest \
        --src ./joey-photos/ \
        --credit "Photo by Joey"

    # Phase 2: Link — associate ingested images with content
    uv run python -m scripts.ingest_images link-exhibition "artist-name" \
        --image-ids 1,2,3 --category showcard

    uv run python -m scripts.ingest_images link-artwork "artwork-slug" \
        --image-ids 4,5 --caption "Detail view"
"""

from __future__ import annotations

import io
import sys
from datetime import datetime, timezone
from pathlib import Path

import click
from PIL import Image as PILImage
from sqlalchemy.orm import Session

from app.config import settings
from app.db import engine
from app.imaging import generate_renditions, rendition_rel_path
from app.models import Image, Rendition
from app.storage import get_storage


_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif"}

# MIME types for storage backends that need them (notably S3)
_MIME_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _detect_images(src: Path) -> list[Path]:
    """Return all image files under *src*, sorted alphabetically."""
    return sorted(
        p for p in src.rglob("*")
        if p.suffix.lower() in _IMAGE_EXTENSIONS and p.is_file()
    )


def _title_from_filename(path: Path) -> str:
    """Derive a human-readable title from a filename.

    Converts ``01_installation_view.jpg`` → ``01 Installation View``.
    """
    stem = path.stem
    # Replace common separators with spaces, collapse runs
    name = stem.replace("_", " ").replace("-", " ").replace(".", " ")
    name = " ".join(name.split())
    return name


def _original_rel_path(src_path: Path) -> str:
    """Compute the relative storage key for an original image.

    Scheme: ``originals/YYYY/basename.ext``
    """
    year = datetime.now(timezone.utc).strftime("%Y")
    return f"{settings.media_originals_dir}/{year}/{src_path.name}"


def _content_type(path: Path) -> str:
    return _MIME_MAP.get(path.suffix.lower(), "application/octet-stream")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.group()
def cli():
    """House Gallery image ingestion tools."""


# ==============================
# ingest
# ==============================


@cli.command()
@click.option("--src", required=True,
              type=click.Path(exists=True, file_okay=False, path_type=Path),
              help="Directory of images to ingest")
@click.option("--credit", default="",
              help="Default photo credit for all images")
@click.option("--alt", default="",
              help="Default alt text for all images")
@click.option("--title-from-filename/--no-title-from-filename",
              default=True,
              help="Derive title from filename (strip ext, replace _ with space)")
@click.option("--dry-run", is_flag=True,
              help="Preview what would be ingested without writing")
@click.option("--batch-size", type=int, default=25,
              help="Images per DB commit (0 = single commit at end)")
def ingest(src, credit, alt, title_from_filename, dry_run, batch_size):
    """Ingest images from SRC directory into the CMS."""
    files = _detect_images(src)
    if not files:
        click.echo("No image files found.", err=True)
        sys.exit(1)

    storage = get_storage()
    total = len(files)
    click.echo(f"Found {total} image(s) to ingest")
    click.echo(f"  storage backend : {type(storage).__name__}")
    click.echo(f"  media root      : {settings.media_root}")
    if batch_size > 0:
        click.echo(f"  batch commit    : every {batch_size} images")
    else:
        click.echo("  batch commit    : disabled (single commit at end)")
    click.echo("")

    results: list[dict] = []
    with Session(engine) as db:
        for idx, filepath in enumerate(files, start=1):
            click.echo(f"  [{idx:>{len(str(total))}}/{total}] {filepath.name} ...",
                       nl=False)

            # --- Decode ---
            data = filepath.read_bytes()
            try:
                with PILImage.open(io.BytesIO(data)) as pil:
                    pil.load()
                    width, height = pil.size
            except Exception as exc:
                click.echo(f"  SKIP (decode failed: {exc})")
                continue

            # --- Metadata ---
            rel_path = _original_rel_path(filepath)
            title = (_title_from_filename(filepath)
                     if title_from_filename else filepath.stem)

            # --- Renditions ---
            rendition_results = generate_renditions(data, storage)
            errors = [r for r in rendition_results if r.error]
            if errors:
                for e in errors:
                    click.echo(f"\n           WARN  {e.key}: {e.error}")

            # --- Dry-run: report only ---
            if dry_run:
                click.echo("  OK (dry-run)")
                results.append({
                    "id": None,
                    "file": filepath.name,
                    "title": title,
                    "width": width,
                    "height": height,
                    "file_size": len(data),
                    "storage_path": rel_path,
                    "renditions": sum(1 for r in rendition_results if not r.error),
                })
                continue

            # --- Store original ---
            try:
                storage.put(rel_path, data, content_type=_content_type(filepath))
            except Exception as exc:
                click.echo(f"  STORE FAILED ({exc})")
                continue

            # --- Image row ---
            img = Image(
                title=title,
                alt=alt or title,
                credit=credit,
                description="",
                file_path=rel_path,
                width=width,
                height=height,
                file_size=len(data),
            )
            db.add(img)
            db.flush()  # get img.id

            # --- Store renditions + create Rendition rows ---
            rend_count = 0
            for rr in rendition_results:
                if rr.error:
                    continue
                r_rel = rendition_rel_path(img.id, rr.key)
                storage.put(r_rel, rr.data, content_type="image/webp")
                db.add(Rendition(
                    image_id=img.id,
                    filter_spec=rr.filter_spec,
                    file_path=r_rel,
                    width=rr.width,
                    height=rr.height,
                    file_size=len(rr.data),
                ))
                rend_count += 1

            click.echo(f"  done  id={img.id}")

            results.append({
                "id": img.id,
                "file": filepath.name,
                "title": title,
                "width": width,
                "height": height,
                "file_size": len(data),
                "storage_path": rel_path,
                "renditions": rend_count,
            })

            # --- Periodic commit ---
            if batch_size > 0 and idx % batch_size == 0:
                db.commit()
                click.echo(f"           committed {idx}/{total}")

        # --- Final commit ---
        if not dry_run and results:
            db.commit()

    # --- Manifest ---
    click.echo("")
    click.echo("─" * 100)
    click.echo(f"{'ID':>6} | {'Title':48} | {'W':5} | {'H':5} | {'Size':9} | Rends")
    click.echo("─" * 100)
    for r in results:
        rid = str(r["id"]) if r["id"] is not None else "—"
        click.echo(
            f"{rid:>6} | {r['title'][:48]:48} | "
            f"{r['width']:5} | {r['height']:5} | "
            f"{r['file_size']:>9} | {r['renditions']}"
        )
    click.echo("─" * 100)
    click.echo(f"{len(results)} image(s) processed ({'dry-run' if dry_run else 'ingested'})")


# ==============================
# link-exhibition
# ==============================


@cli.command()
@click.argument("slug")
@click.option("--image-ids", required=True,
              help="Comma-separated list of image IDs")
@click.option("--category",
              type=click.Choice(
                  ["showcard", "installation", "opening_reception", "in_progress"]
              ),
              default="installation",
              help="Exhibition photo category")
def link_exhibition(slug, image_ids, category):
    """Link ingested images to an exhibition as ExhibitionPhoto rows."""
    ids = [int(x.strip()) for x in image_ids.split(",")]

    from sqlalchemy import func, select

    from app.models import Exhibition, ExhibitionPhoto, Image

    with Session(engine) as db:
        exhibition = db.execute(
            select(Exhibition).where(Exhibition.slug == slug)
        ).scalars().first()

        if exhibition is None:
            click.echo(f"Exhibition '{slug}' not found.", err=True)
            sys.exit(1)

        # Determine next sort_order
        max_order = db.execute(
            select(func.coalesce(func.max(ExhibitionPhoto.sort_order), -1))
            .where(ExhibitionPhoto.exhibition_id == exhibition.id)
        ).scalar()

        added = 0
        skipped = 0
        for i, img_id in enumerate(ids, start=1):
            img = db.get(Image, img_id)
            if img is None:
                click.echo(f"  SKIP: Image {img_id} not found")
                skipped += 1
                continue

            exists = db.execute(
                select(ExhibitionPhoto).where(
                    ExhibitionPhoto.exhibition_id == exhibition.id,
                    ExhibitionPhoto.image_id == img_id,
                )
            ).first()
            if exists:
                click.echo(f"  SKIP: Image {img_id} already linked")
                skipped += 1
                continue

            db.add(ExhibitionPhoto(
                exhibition_id=exhibition.id,
                image_id=img_id,
                category=category,
                sort_order=max_order + i,
            ))
            added += 1

        db.commit()
        click.echo(f"Linked {added} image(s) to exhibition '{slug}' as {category}")
        if skipped:
            click.echo(f"  skipped: {skipped}")


# ==============================
# link-artwork
# ==============================


@cli.command()
@click.argument("slug")
@click.option("--image-ids", required=True,
              help="Comma-separated list of image IDs")
@click.option("--caption", default="",
              help="Caption for the artwork image")
def link_artwork(slug, image_ids, caption):
    """Link ingested images to an artwork as ArtworkImage rows."""
    ids = [int(x.strip()) for x in image_ids.split(",")]

    from sqlalchemy import func, select

    from app.models import Artwork, ArtworkImage, Image

    with Session(engine) as db:
        artwork = db.execute(
            select(Artwork).where(Artwork.slug == slug)
        ).scalars().first()

        if artwork is None:
            click.echo(f"Artwork '{slug}' not found.", err=True)
            sys.exit(1)

        max_order = db.execute(
            select(func.coalesce(func.max(ArtworkImage.sort_order), -1))
            .where(ArtworkImage.artwork_id == artwork.id)
        ).scalar()

        added = 0
        skipped = 0
        for i, img_id in enumerate(ids, start=1):
            img = db.get(Image, img_id)
            if img is None:
                click.echo(f"  SKIP: Image {img_id} not found")
                skipped += 1
                continue

            exists = db.execute(
                select(ArtworkImage).where(
                    ArtworkImage.artwork_id == artwork.id,
                    ArtworkImage.image_id == img_id,
                )
            ).first()
            if exists:
                click.echo(f"  SKIP: Image {img_id} already linked")
                skipped += 1
                continue

            db.add(ArtworkImage(
                artwork_id=artwork.id,
                image_id=img_id,
                caption=caption,
                sort_order=max_order + i,
            ))
            added += 1

        db.commit()
        click.echo(f"Linked {added} image(s) to artwork '{slug}'")
        if skipped:
            click.echo(f"  skipped: {skipped}")


if __name__ == "__main__":
    cli()