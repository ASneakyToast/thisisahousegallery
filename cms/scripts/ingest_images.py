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

import sys
from pathlib import Path

import click


@click.group()
def cli():
    """House Gallery image ingestion tools."""


# ---------------------------------------------------------------------------
# ingest — scan a directory, process images, store files, create DB records
# ---------------------------------------------------------------------------


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
def ingest(src, credit, alt, title_from_filename, dry_run):
    """Ingest images from SRC directory into the CMS."""
    click.echo(f"Ingesting from: {src}")
    click.echo(f"  credit          : {credit}")
    click.echo(f"  alt             : {alt}")
    click.echo(f"  title from file : {title_from_filename}")
    click.echo(f"  dry-run         : {dry_run}")
    click.echo("(not yet implemented)")


# ---------------------------------------------------------------------------
# link-exhibition — associate ingested images with an exhibition
# ---------------------------------------------------------------------------


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
    click.echo(f"Linking images {ids} to exhibition '{slug}' as {category}")
    click.echo("(not yet implemented)")


# ---------------------------------------------------------------------------
# link-artwork — associate ingested images with an artwork
# ---------------------------------------------------------------------------


@cli.command()
@click.argument("slug")
@click.option("--image-ids", required=True,
              help="Comma-separated list of image IDs")
@click.option("--caption", default="",
              help="Caption for the artwork image")
def link_artwork(slug, image_ids, caption):
    """Link ingested images to an artwork as ArtworkImage rows."""
    ids = [int(x.strip()) for x in image_ids.split(",")]
    click.echo(f"Linking images {ids} to artwork '{slug}'")
    click.echo("(not yet implemented)")


if __name__ == "__main__":
    cli()