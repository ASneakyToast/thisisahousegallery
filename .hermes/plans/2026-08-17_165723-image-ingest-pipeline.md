# Image Ingest Pipeline — Script + Skill

> **For Hermes:** Implement this plan task-by-task. Reuse existing `app/imaging.py`, `app/storage.py`, and model definitions.

**Goal:** Replace Joel's manual download-resize-upload workflow with a reliable script (`cms/scripts/ingest_images.py`) and a Hermes skill that guides the agent through the process.

**Architecture:** A deterministic Python script (`ingest_images.py`) does one thing — take a directory of images, process them through the existing rendition pipeline, and create DB records. The skill teaches the agent how to use it: download from Drive, infer metadata from folder/filename context, ask Joel when ambiguous, use vision as fallback, then run ingest + linking as separate passes.

**Tech Stack:** Python 3.11, SQLAlchemy, Pillow (existing), `app.imaging`, `app.storage`, `app.models`

---

## Task 1: Scaffold the scripts directory + CLI skeleton

**Objective:** Create `cms/scripts/` dir and the main script with click subcommands

**Files:**
- Create: `cms/scripts/__init__.py` (empty)
- Create: `cms/scripts/ingest_images.py` (skeleton with click CLI)

**Step 1: Create the directory**

```bash
mkdir -p cms/scripts
touch cms/scripts/__init__.py
```

**Step 2: Write the skeleton**

The script uses `click` for CLI (lightweight, already in the CMS venv via FastAPI/SQLAdmin deps, or `uv pip install click`).

```python
#!/usr/bin/env python
"""Ingest images: process, store, and create DB records.

Usage:
    cd cms/
    uv run python -m scripts.ingest_images ingest --src ./joey-photos/ --credit "Photo by Joey"
    uv run python -m scripts.ingest_images link-exhibition --slug "artist-name" --image-ids 1,2,3 --category showcard
    uv run python -m scripts.ingest_images link-artwork --slug "artwork-slug" --image-ids 4,5 --caption "Detail"
"""

from __future__ import annotations

import sys
from pathlib import Path

import click


@click.group()
def cli():
    """House Gallery image ingestion tools."""


@cli.command()
@click.option("--src", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path),
              help="Directory of images to ingest")
@click.option("--credit", default="", help="Default photo credit for all images")
@click.option("--alt", default="", help="Default alt text for all images")
@click.option("--title-from-filename/--no-title-from-filename", default=True,
              help="Derive title from filename (strip extension, replace _ with space)")
@click.option("--dry-run", is_flag=True, help="Preview without writing to DB or storage")
def ingest(src, credit, alt, title_from_filename, dry_run):
    """Ingest images from SRC directory into the CMS."""
    click.echo(f"Ingesting from: {src}")
    click.echo(f"  credit: {credit}")
    click.echo(f"  alt: {alt}")
    click.echo(f"  title from filename: {title_from_filename}")
    click.echo(f"  dry-run: {dry_run}")


@cli.command()
@click.argument("slug")
@click.option("--image-ids", required=True, help="Comma-separated list of image IDs")
@click.option("--category", type=click.Choice(["showcard", "installation", "opening_reception", "in_progress"]),
              default="installation", help="Photo category for the exhibition")
def link_exhibition(slug, image_ids, category):
    """Link ingested images to an exhibition as exhibition photos."""
    ids = [int(x.strip()) for x in image_ids.split(",")]
    click.echo(f"Linking images {ids} to exhibition '{slug}' as {category}")


@cli.command()
@click.argument("slug")
@click.option("--image-ids", required=True, help="Comma-separated list of image IDs")
@click.option("--caption", default="", help="Caption for the artwork image")
def link_artwork(slug, image_ids, caption):
    """Link ingested images to an artwork."""
    ids = [int(x.strip()) for x in image_ids.split(",")]
    click.echo(f"Linking images {ids} to artwork '{slug}'")


if __name__ == "__main__":
    cli()
```

**Step 3: Verify skeleton works**

```bash
cd /c/Users/Joel/Code/personal/thisisahousegallery/cms
uv run python -m scripts.ingest_images --help
uv run python -m scripts.ingest_images ingest --help
uv run python -m scripts.ingest_images link-exhibition --help
uv run python -m scripts.ingest_images link-artwork --help
```

Expected: each help text prints correctly.

**Step 4: Commit**

```bash
git add cms/scripts/
git commit -m "feat: scaffold ingest_images script with click CLI skeleton"
```

---

## Task 2: Implement the `ingest` subcommand

**Objective:** Full image processing pipeline — scan directory, decode images, generate renditions, store via Storage, create DB records.

**Files:**
- Modify: `cms/scripts/ingest_images.py`
- (Read-only references): `cms/app/imaging.py`, `cms/app/storage.py`, `cms/app/models.py`, `cms/app/db.py`, `cms/app/config.py`

**Imports needed:**

```python
import io
import os
from datetime import datetime
from pathlib import Path

from PIL import Image as PILImage

from app.config import settings
from app.db import engine
from app.imaging import generate_renditions, rendition_rel_path
from app.models import Image, Rendition
from app.storage import get_storage
from sqlalchemy.orm import Session
```

**Step 1: Implement the ingest logic**

The `ingest` subcommand should:

1. **Scan `--src`** for image files (`.jpg`, `.jpeg`, `.png`, `.webp`, `.tiff`, `.tif` — case-insensitive)
2. **For each image:**
   a. Read bytes
   b. Open with PIL to get dimensions
   c. Open original file size from bytes
   d. Derive title from filename (strip extension, replace `_`/`-` with spaces, title-case) OR use a sequential title if `--no-title-from-filename`
   e. Generate renditions via `generate_renditions(data)`
   f. Compute storage path for original: `originals/{year}/{filename}`
   g. Store original via `storage.put(original_rel_path, data, content_type)`
   h. Store each rendition via `storage.put(rendition_rel_path(...), rendition.data, content_type="image/webp")`
   i. (Skip DB writes if `--dry-run`)
   j. Create `Image` row with extracted metadata
   k. Create `Rendition` rows for each generated rendition
3. **Print manifest table**

The storage path for originals should follow the existing pattern in config: `media_originals_dir = "originals"`. So originals go to `originals/2026/artist-exhibition/filename.jpg` or similar. Let's use `originals/{year}/{filename}` as a simple default.

Actually, looking at the existing code more carefully — the `generate_renditions.py` script takes originals from a backup dir and creates renditions. The `Image.file_path` stores the relative path to the original. For our ingest script, we'll store the original under:

```
originals/{YYYY}/{basename}
```

And the renditions go to:
```
renditions/{image_id}/{key}.webp
```

(Note: `image_id` isn't known until we create the Image row. So for local storage we'd need a two-phase: create the Image row first to get the ID, then store renditions. Or we could use a deterministic path based on filename. Let me think...)

Actually, the existing code stores renditions using `rendition_rel_path(image_id, key)` — so it needs the DB id. The clean approach:

1. First pass: decode images, collect metadata (width, height, file_size). No storage yet.
2. Create Image rows in DB (gets IDs).
3. Second pass: generate renditions, store both originals and renditions using the IDs.

Or even simpler: create Image row first (without file_path... no, file_path is NOT NULL).

Hmm, let me rethink. The flow should be:

1. For each image, read bytes
2. Derive metadata (title, alt, credit from CLI args)
3. We need to store the original FIRST to get the URL that goes in Image.file_path
4. Then create the Image row (now we have the ID)
5. Then generate and store renditions using the ID

Actually, wait — `Image.file_path` is just the relative path (like `originals/2026/photo.jpg`), not the URL. The URL is computed by the storage backend. So we can compute the rel_path before storing, store the bytes, create the Image row, then store renditions.

Let me code this properly.

```python
def _image_rel_path(src_path: Path) -> str:
    """Compute the relative storage path for an original image."""
    year = datetime.utcnow().strftime("%Y")
    return f"{settings.media_originals_dir}/{year}/{src_path.name}"

def _detect_content_type(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }.get(ext, "application/octet-stream")

def _title_from_filename(path: Path) -> str:
    stem = path.stem
    # Replace separators with spaces, strip numbers prefix like "01_"
    name = stem.replace("_", " ").replace("-", " ").strip()
    return name.title()
```

OK, now let me think about the full ingest flow:

```python
def ingest(src, credit, alt, title_from_filename, dry_run):
    storage = get_storage()
    image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif"}
    
    # Collect all image files
    files = sorted([
        p for p in src.rglob("*")
        if p.suffix.lower() in image_extensions and p.is_file()
    ])
    
    if not files:
        click.echo("No image files found.", err=True)
        sys.exit(1)
    
    click.echo(f"Found {len(files)} image(s)")
    
    results = []
    with Session(engine) as db:
        for i, filepath in enumerate(files, 1):
            click.echo(f"[{i}/{len(files)}] {filepath.name}...", nl=False)
            
            data = filepath.read_bytes()
            
            # Get dimensions
            try:
                with PILImage.open(io.BytesIO(data)) as pil:
                    pil.load()
                    width, height = pil.size
            except Exception as e:
                click.echo(f" SKIP (decode failed: {e})")
                continue
            
            # Compute storage paths
            rel_path = _image_rel_path(filepath)
            title = _title_from_filename(filepath) if title_from_filename else filepath.stem
            
            # Generate renditions
            rendition_results = generate_renditions(data, storage)
            has_error = any(r.error for r in rendition_results)
            
            if dry_run:
                click.echo(" OK (dry-run)")
                results.append({
                    "file": filepath.name,
                    "title": title,
                    "width": width,
                    "height": height,
                    "file_size": len(data),
                    "storage_path": rel_path,
                    "renditions": len(rendition_results),
                })
                continue
            
            # Store original
            ct = _detect_content_type(filepath)
            try:
                storage.put(rel_path, data, content_type=ct)
            except Exception as e:
                click.echo(f" STORE ERR: {e}")
                continue
            
            # Create Image row
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
            
            # Store renditions + create Rendition rows
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
            
            click.echo(f" done (id={img.id})")
            results.append({
                "id": img.id,
                "file": filepath.name,
                "title": title,
                "width": width,
                "height": height,
                "file_size": len(data),
                "storage_path": rel_path,
                "renditions": sum(1 for r in rendition_results if not r.error),
            })
        
        if not dry_run and results:
            db.commit()
    
    # Print manifest
    click.echo("\n--- Manifest ---")
    click.echo(f"{'ID':>5} | {'Title':40} | {'W':5} | {'H':5} | {'Size':8} | {'Rends':6}")
    click.echo("-" * 80)
    for r in results:
        click.echo(f"{r.get('id', '—'):>5} | {r['title'][:40]:40} | {r['width']:5} | {r['height']:5} | {r['file_size']:8} | {r['renditions']:6}")
```

That's the core implementation.

**Step 2: Test with a real image**

Create a test dir with one image:

```bash
cd /c/Users/Joel/Code/personal/thisisahousegallery

# Create a test image
mkdir -p /tmp/ingest-test
convert -size 800x600 xc:gray /tmp/ingest-test/test_image.jpg

# Dry run
cd cms
uv run python -m scripts.ingest_images ingest --src /tmp/ingest-test --credit "Test" --dry-run

# Real run
uv run python -m scripts.ingest_images ingest --src /tmp/ingest-test --credit "Test"
```

Expected: Image appears in DB, renditions appear under `cms/media/renditions/{id}/`, original under `cms/media/originals/2026/`.

**Step 3: Verify via API**

```bash
curl http://localhost:8000/v1/images/1 | python -m json.tool
```

Expected: returns image metadata with `file_url` pointing to the stored original and `renditions` array with 3 WebP URLs.

**Step 4: Commit**

```bash
git add cms/scripts/ingest_images.py
git commit -m "feat: implement ingest subcommand for image processing pipeline"
```

---

## Task 3: Implement `link-exhibition` subcommand

**Objective:** Link previously ingested images to an exhibition via the ExhibitionPhoto model.

**Files:**
- Modify: `cms/scripts/ingest_images.py`

**Step 1: Implement link-exhibition**

```python
@cli.command()
@click.argument("slug")
@click.option("--image-ids", required=True, help="Comma-separated list of image IDs")
@click.option("--category", type=click.Choice(["showcard", "installation", "opening_reception", "in_progress"]),
              default="installation", help="Photo category")
def link_exhibition(slug, image_ids, category):
    """Link images to an exhibition as ExhibitionPhoto rows."""
    ids = [int(x.strip()) for x in image_ids.split(",")]
    
    from app.models import Exhibition, ExhibitionPhoto, Image
    from sqlalchemy import select
    
    with Session(engine) as db:
        exhibition = db.execute(
            select(Exhibition).where(Exhibition.slug == slug)
        ).scalars().first()
        
        if exhibition is None:
            click.echo(f"Exhibition '{slug}' not found.", err=True)
            sys.exit(1)
        
        # Find existing photos to determine next sort_order
        max_order = db.execute(
            select(func.coalesce(func.max(ExhibitionPhoto.sort_order), -1))
            .where(ExhibitionPhoto.exhibition_id == exhibition.id)
        ).scalar()
        
        added = 0
        skipped = 0
        for i, img_id in enumerate(ids, 1):
            # Verify image exists
            img = db.get(Image, img_id)
            if img is None:
                click.echo(f"  SKIP: Image {img_id} not found")
                skipped += 1
                continue
            
            # Avoid duplicates
            exists = db.execute(
                select(ExhibitionPhoto).where(
                    ExhibitionPhoto.exhibition_id == exhibition.id,
                    ExhibitionPhoto.image_id == img_id,
                )
            ).first()
            if exists:
                click.echo(f"  SKIP: Image {img_id} already linked to this exhibition")
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
        click.echo(f"Linked {added} images to exhibition '{slug}' as {category}")
        if skipped:
            click.echo(f"  skipped: {skipped}")
```

**Step 2: Verify**

Point at an existing exhibition:

```bash
uv run python -m scripts.ingest_images link-exhibition "artist-name" --image-ids 1 --category showcard
```

Check via API: `curl http://localhost:8000/v1/exhibitions/artist-name | jq '.photos'`

Expected: the photo appears in the exhibition's photos array with the correct category.

**Step 3: Commit**

```bash
git add cms/scripts/ingest_images.py
git commit -m "feat: implement link-exhibition subcommand"
```

---

## Task 4: Implement `link-artwork` subcommand

**Objective:** Link images to a specific artwork via the ArtworkImage model.

**Files:**
- Modify: `cms/scripts/ingest_images.py`

**Step 1: Implement link-artwork**

```python
@cli.command()
@click.argument("slug")
@click.option("--image-ids", required=True, help="Comma-separated list of image IDs")
@click.option("--caption", default="", help="Caption for the artwork image")
def link_artwork(slug, image_ids, caption):
    """Link images to an artwork as ArtworkImage rows."""
    ids = [int(x.strip()) for x in image_ids.split(",")]
    
    from app.models import Artwork, ArtworkImage, Image
    from sqlalchemy import select, func
    
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
        for i, img_id in enumerate(ids, 1):
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
        click.echo(f"Linked {added} images to artwork '{slug}'")
        if skipped:
            click.echo(f"  skipped: {skipped}")
```

**Step 2: Verify**

```bash
uv run python -m scripts.ingest_images link-artwork "artwork-slug" --image-ids 1
curl http://localhost:8000/v1/artworks/artwork-slug | jq '.images'
```

**Step 3: Commit**

```bash
git add cms/scripts/ingest_images.py
git commit -m "feat: implement link-artwork subcommand"
```

---

## Task 5: Write the Hermes skill

**Objective:** A SKILL.md that teaches the agent the complete workflow for handling Joey's Drive images.

**Files:**
- Create: skill (via `skill_manage`)

**Skill content:**

```markdown
---
name: housegallery-image-ingest
description: From a Google Drive folder of images, ingest into the CMS and link to content.
version: 1.0.0
---

# House Gallery Image Ingest

Use when Joel says Joey sent images in a Google Drive folder and they need to go into the gallery CMS.

## Workflow

### 1. Download from Google Drive

- Ask Joel for the Drive link
- Use `computer_use` to open the link in the browser
- Download the folder as a ZIP (Drive's "Download all" option)
- Extract to a temp dir: `C:/Users/Joel/housegallery-ingest/<descriptive-name>/`

### 2. Examine the folder

List the contents and look for clues:
- **Folder name** — often names the exhibition or artist (e.g. "Devan Ponce showcard")
- **Filenames** — may hint at category ("installation_01.jpg", "showcard_front.jpg", "ART001_hero.jpg")
- **Number of images** — 1-2 is usually just a showcard; 10+ is installation/opening photos

### 3. Determine metadata

Try in order:
1. **Folder name + filenames** — if clear (e.g. folder "Devan Ponce" + files "installation_01.jpg"), use them
2. **Ask Joel** — "I have 15 photos in a folder — do you know which exhibition? Anything that's the showcard vs installation?"
3. **Vision fallback** — if Joel isn't sure, use `vision_analyze` on a few sample images:
   - Showcard = promotional poster/flyer with text, dates, artist name
   - Installation = gallery walls with artwork hung
   - Opening reception = people at an event

### 4. Run the ingest

```bash
cd C:/Users/Joel/Code/personal/thisisahousegallery/cms
uv run python -m scripts.ingest_images ingest --src <path> --credit "Photo by Joey"
```

### 5. Verify

Check a sample image via the API:

```bash
curl http://localhost:8000/v1/images/<id> | python -m json.tool
```

Verify: `file_url` exists, `renditions` has 3 entries with `.webp` URLs.

### 6. Link to content

**If exhibition photos (showcard/installation):**
```bash
uv run python -m scripts.ingest_images link-exhibition "<slug>" \
    --image-ids <ids> --category <showcard|installation|opening_reception>
```

**If artwork images:**
```bash
uv run python -m scripts.ingest_images link-artwork "<slug>" \
    --image-ids <ids> --caption "<caption>"
```

**If profile image for an artist:** this needs the script's `link-artwork` or manual DB update via the API/sqladmin. For now, note it as a limitation.

### 7. Final verification

Fetch the exhibition/artwork via the API and confirm the images appear:

```bash
curl http://localhost:8000/v1/exhibitions/<slug>
# Check photos array has the right images with URLs
```

## Pitfalls

- **Don't commit media files** — only the script and skill go in git
- **Large batches** — commit DB periodically (the current code commits at the end; for 50+ images, add periodic commits)
- **Duplicate images** — the script doesn't deduplicate by hash; it creates new Image rows each time. Clean up stale rows via sqladmin if needed.
- **Storage backend** — respects whatever `MEDIA_STORAGE` is set to. With `local`, files go to `cms/media/`. With `s3`, they go to the S3 bucket.
- **Temp files** — clean up `C:/Users/Joel/housegallery-ingest/` after successful ingest
```

**Step 2: Save the skill**

```bash
# Use skill_manage tool
```

**Step 3: Verify the skill loads**

```bash
# Load it with skill_view('housegallery-image-ingest')
```

---

## Risks & Open Questions

1. **Image dedup** — current script always creates new Image rows. A future improvement: detect duplicates by file hash (`--dedup` flag).
2. **Batch commit for 50+ images** — the initial implementation commits once at the end. For very large batches, add periodic commits (every 25 images).
3. **S3 migration** — when we flip `MEDIA_STORAGE=s3`, the script automatically uses S3Storage. No code change needed.
4. **Deleting ingested images** — no inverse command yet. Use sqladmin at `http://localhost:8000/admin` to delete Image rows (cascades to renditions).
5. **Artist profile images** — not handled by `link-artwork` or `link-exhibition`. Could add a `link-artist-profile` subcommand later or handle manually.