"""Image rendition pipeline.

Reads an original image and generates the agreed WebP rendition set,
mirroring the design decision (Q2): hi-res preserved, plus web renditions.

Rendition set (from design §10.2 / images.py):
  - thumbnail_400        : width-400  | WebP q82
  - web_optimized_1200   : width-1200 | WebP q85
  - high_quality_2400    : max-2400x2400 | WebP q90   (hi-res cap, ~4K-ish)

Full-res originals are preserved separately (they are copied / archived, never
served in the page).
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field

from PIL import Image

from app.storage import Storage, get_storage


@dataclass(frozen=True)
class RenditionSpec:
    key: str
    filter_spec: str
    width: int | None = None
    max_dim: int | None = None
    quality: int = 85


RENDITIONS: tuple[RenditionSpec, ...] = (
    RenditionSpec("thumbnail_400", "width-400|format-webp|webpquality-82", width=400, quality=82),
    RenditionSpec("web_optimized_1200", "width-1200|format-webp|webpquality-85", width=1200, quality=85),
    RenditionSpec("high_quality_2400", "max-2400x2400|format-webp|webpquality-90", max_dim=2400, quality=90),
)


@dataclass
class GeneratedRendition:
    key: str
    filter_spec: str
    data: bytes
    width: int
    height: int
    url: str = ""
    error: str = ""


def _resize(im: Image.Image, spec: RenditionSpec) -> Image.Image:
    im = im.convert("RGB")
    if spec.width:
        ratio = spec.width / im.width
        new_h = max(1, round(im.height * ratio))
        return im.resize((spec.width, new_h), Image.LANCZOS)
    if spec.max_dim:
        longest = max(im.width, im.height)
        if longest <= spec.max_dim:
            return im
        ratio = spec.max_dim / longest
        new_w = max(1, round(im.width * ratio))
        new_h = max(1, round(im.height * ratio))
        return im.resize((new_w, new_h), Image.LANCZOS)
    return im


def generate_renditions(data: bytes, storage: Storage | None = None) -> list[GeneratedRendition]:
    """Generate the full rendition set for an original image's bytes."""
    storage = storage or get_storage()
    results: list[GeneratedRendition] = []
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception as e:  # noqa: BLE001 - report, don't crash the batch
        return [
            GeneratedRendition(
                key="error", filter_spec="", data=b"", width=0, height=0,
                error=f"decode failed: {e}",
            )
        ]

    for spec in RENDITIONS:
        try:
            resized = _resize(im, spec)
            buf = io.BytesIO()
            resized.save(buf, format="WEBP", quality=spec.quality, method=6)
            results.append(
                GeneratedRendition(
                    key=spec.key,
                    filter_spec=spec.filter_spec,
                    data=buf.getvalue(),
                    width=resized.width,
                    height=resized.height,
                )
            )
        except Exception as e:  # noqa: BLE001
            results.append(
                GeneratedRendition(
                    key=spec.key, filter_spec=spec.filter_spec, data=b"",
                    width=0, height=0, error=str(e),
                )
            )
    return results


def rendition_rel_path(image_id: int, key: str) -> str:
    return f"renditions/{image_id}/{key}.webp"
