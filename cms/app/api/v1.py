"""Public read-only /v1 API.

Serves the content a static frontend build needs. Read-only, no auth yet
(auth/tenant keying is a later phase per the design doc).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db import SessionLocal
from app.models import (
    Artist,
    Artwork,
    Event,
    Exhibition,
    ExhibitionPhoto,
    HomePage,
    Image,
    SiteSettings,
    Tag,
)
from app.schemas import (
    ArtistDetailOut,
    ArtistOut,
    ArtworkOut,
    EventOut,
    ExhibitionDetailOut,
    ExhibitionOut,
    ExhibitionsIndexImage,
    ExhibitionsIndexPageOut,
    ExhibitionsIndexShow,
    HomeOut,
    HomePageOut,
    HomeShowOut,
    ImageOut,
    RenditionOut,
    SiteSettingsOut,
    TagOut,
)
from app.storage import get_storage

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/site-settings", response_model=SiteSettingsOut)
def get_site_settings(db: Session = Depends(get_db)):
    settings = db.execute(select(SiteSettings).order_by(SiteSettings.id)).scalars().first()
    if settings is None:
        raise HTTPException(status_code=404, detail="Site settings not configured")
    return settings


@router.get("/home", response_model=HomeOut)
def get_home(db: Session = Depends(get_db)):
    home = db.execute(select(HomePage).order_by(HomePage.id)).scalars().first()
    if home is None:
        return HomeOut(intro="", floating_images=[])
    ids = home.floating_image_ids or []
    images = []
    if ids:
        rows = {
            r.id: r
            for r in db.execute(select(Image).where(Image.id.in_(ids))).scalars().all()
        }
        images = [rows[i] for i in ids if i in rows]
    return HomeOut(intro=home.intro or "", floating_images=images)


@router.get("/tags", response_model=list[TagOut])
def list_tags(db: Session = Depends(get_db)):
    return db.execute(select(Tag).order_by(Tag.name)).scalars().all()


@router.get("/events", response_model=list[EventOut])
def list_events(
    event_type: Optional[str] = Query(default=None),
    featured: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db),
):
    q = select(Event).options(
        joinedload(Event.related_exhibition),
        joinedload(Event.featured_image).joinedload(Image.renditions),
    )
    if event_type:
        q = q.where(Event.event_type == event_type)
    if featured is not None:
        q = q.where(Event.featured_on_schedule == featured)
    rows = db.execute(q.order_by(Event.start_date)).unique().scalars().all()
    return rows


@router.get("/exhibitions", response_model=list[ExhibitionOut])
def list_exhibitions(db: Session = Depends(get_db)):
    rows = (
        db.execute(
            select(Exhibition)
            .options(
                joinedload(Exhibition.artists),
                joinedload(Exhibition.artworks),
                joinedload(Exhibition.listing_image).joinedload(Image.renditions),
            )
            .order_by(Exhibition.start_date.desc())
        )
        .unique()
        .scalars()
        .all()
    )
    return rows


@router.get("/exhibitions/{slug}", response_model=ExhibitionDetailOut)
def get_exhibition(slug: str, db: Session = Depends(get_db)):
    row = (
        db.execute(
            select(Exhibition)
            .options(
                joinedload(Exhibition.artists),
                joinedload(Exhibition.artworks),
                joinedload(Exhibition.listing_image).joinedload(Image.renditions),
                joinedload(Exhibition.photos).joinedload(ExhibitionPhoto.image),
            )
            .where(Exhibition.slug == slug)
        )
        .unique()
        .scalars()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Exhibition not found")
    return row


@router.get("/artists", response_model=list[ArtistOut])
def list_artists(db: Session = Depends(get_db)):
    rows = (
        db.execute(
            select(Artist)
            .options(
                joinedload(Artist.profile_image).joinedload(Image.renditions),
            )
            .order_by(Artist.name)
        )
        .unique()
        .scalars()
        .all()
    )
    return rows


@router.get("/artists/{slug}", response_model=ArtistDetailOut)
def get_artist(slug: str, db: Session = Depends(get_db)):
    row = (
        db.execute(
            select(Artist)
            .options(
                joinedload(Artist.profile_image).joinedload(Image.renditions),
                joinedload(Artist.artworks)
                .joinedload(Artwork.images)
                .joinedload(Image.renditions),
            )
            .where(Artist.slug == slug)
        )
        .unique()
        .scalars()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    return row


@router.get("/artworks", response_model=list[ArtworkOut])
def list_artworks(
    artist: Optional[str] = Query(default=None),
    tag: Optional[str] = Query(default=None),
    exhibition: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    q = select(Artwork).options(
        joinedload(Artwork.artists),
        joinedload(Artwork.images).joinedload(Image.renditions),
        joinedload(Artwork.tags),
    )
    if artist:
        q = q.join(Artwork.artists).where(Artist.slug == artist)
    if tag:
        q = q.join(Artwork.tags).where(Tag.slug == tag)
    if exhibition:
        q = q.join(Artwork.exhibitions).where(Exhibition.slug == exhibition)
    rows = db.execute(q.order_by(Artwork.title)).unique().scalars().all()
    return rows


@router.get("/artworks/{slug}", response_model=ArtworkOut)
def get_artwork(slug: str, db: Session = Depends(get_db)):
    row = (
        db.execute(
            select(Artwork)
            .options(
                joinedload(Artwork.artists),
                joinedload(Artwork.images).joinedload(Image.renditions),
                joinedload(Artwork.tags),
            )
            .where(Artwork.slug == slug)
        )
        .unique()
        .scalars()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Artwork not found")
    return row


@router.get("/images/{image_id}", response_model=ImageOut)
def get_image(image_id: int, db: Session = Depends(get_db)):
    row = (
        db.execute(
            select(Image)
            .options(joinedload(Image.renditions))
            .where(Image.id == image_id)
        )
        .unique()
        .scalars()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return row


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# BFF / page-shaped endpoints
# ---------------------------------------------------------------------------
def _best_image_url(img: Optional[Image], max_width: int = 400) -> Optional[str]:
    """Pick the smallest rendition >= max_width (else largest), return its URL.

    Mirrors the frontend `bestImageUrl` helper so image-selection logic lives
    in the backend for the page-shaped endpoints. Note we build the URL from
    `file_path` via storage (renditions carry no URL until the Pydantic
    validator populates it on the output schema).
    """
    if img is None:
        return None
    storage = get_storage()
    renditions = sorted(img.renditions, key=lambda r: r.width)
    if not renditions:
        return storage.url(img.file_path)
    for r in renditions:
        if r.width >= max_width:
            return storage.url(r.file_path)
    return storage.url(renditions[-1].file_path)


def _show_card_image_url(ex) -> Optional[str]:
    """Resolve an exhibition's homepage thumbnail: showcard photo, else
    listing image, else the first artwork's first image (best at 400px)."""
    if getattr(ex, "photos", None):
        for p in ex.photos:
            if p.category == "showcard" and p.image:
                return _best_image_url(p.image, 400)
    if ex.listing_image:
        return _best_image_url(ex.listing_image, 400)
    for a in (ex.artworks or []):
        if a.images:
            return _best_image_url(a.images[0], 400)
    return None


@router.get("/pages/home", response_model=HomePageOut)
def get_page_home(db: Session = Depends(get_db)):
    """One payload for the static homepage: site settings + hero + shows.

    Collapses what the Astro homepage previously fetched as ~17 requests
    (site-settings + exhibitions + N detail + home) into a single small call.
    Shows carry a pre-resolved thumbnail URL and artist names only (no nested
    artwork/rendition trees), so the payload is light.
    """
    settings = db.execute(select(SiteSettings).order_by(SiteSettings.id)).scalars().first()
    home = db.execute(select(HomePage).order_by(HomePage.id)).scalars().first()

    # Hero floating images (honour ordering), best at 400px
    floating_urls: list[str] = []
    if home and home.floating_image_ids:
        ids = list(home.floating_image_ids)
        rows = {
            r.id: r
            for r in db.execute(select(Image).where(Image.id.in_(ids))).scalars().all()
        }
        floating_urls = [
            url
            for i in ids
            if (i in rows) and (url := _best_image_url(rows[i], 400)) is not None
        ]

    # Shows (newest first), each with a resolved thumbnail
    exhibitions = (
        db.execute(
            select(Exhibition)
            .options(
                joinedload(Exhibition.artists),
                joinedload(Exhibition.artworks).selectinload(Artwork.images).selectinload(Image.renditions),
                joinedload(Exhibition.listing_image).joinedload(Image.renditions),
                joinedload(Exhibition.photos).joinedload(ExhibitionPhoto.image).selectinload(Image.renditions),
            )
            .order_by(Exhibition.start_date.desc())
        )
        .unique()
        .scalars()
        .all()
    )

    shows = [
        HomeShowOut(
            slug=ex.slug,
            title=ex.title,
            listing_title=ex.listing_title,
            listing_summary=ex.listing_summary,
            start_date=ex.start_date,
            end_date=ex.end_date,
            artists=[a.name for a in (ex.artists or [])],
            image_url=_show_card_image_url(ex),
        )
        for ex in exhibitions
    ]

    return HomePageOut(
        site_title=(settings.site_title if settings else ""),
        tagline=(settings.tagline if settings else ""),
        intro=(home.intro if home else ""),
        floating_image_urls=floating_urls,
        shows=shows,
    )


# ---------------------------------------------------------------------------
# BFF — exhibitions index page
# ---------------------------------------------------------------------------
def _rendition_urls(img, storage) -> tuple[Optional[str], Optional[str]]:
    """Return (thumbnail_url, full_url) for an Image, best at 400 / 1600 px."""
    if not img:
        return (None, None)
    rends = sorted(img.renditions, key=lambda r: r.width)
    thumbs, fulls = None, None
    for r in rends:
        url = storage.url(r.file_path)
        if r.width >= 400 and thumbs is None:
            thumbs = url
        if r.width >= 1600 and fulls is None:
            fulls = url
    if thumbs is None and rends:
        thumbs = storage.url(rends[-1].file_path)
    if fulls is None and rends:
        fulls = storage.url(rends[-1].file_path)
    return (thumbs or storage.url(img.file_path), fulls or storage.url(img.file_path))


@router.get("/pages/exhibitions", response_model=ExhibitionsIndexPageOut)
def get_pages_exhibitions(db: Session = Depends(get_db)):
    """One payload for the exhibitions index page, pre-assembled.

    Replicates the legacy filter: first showcard → installation + artwork
    covers (shuffled) → remaining showcards. Opening-reception and in-progress
    photos are excluded. Every gallery image carries pre-resolved thumbnail
    (400px) and full-size (1600px) URLs.
    """
    storage = get_storage()

    exhibitions = (
        db.execute(
            select(Exhibition)
            .options(
                joinedload(Exhibition.artists),
                joinedload(Exhibition.artworks).selectinload(Artwork.images).selectinload(Image.renditions),
                joinedload(Exhibition.listing_image).joinedload(Image.renditions),
                joinedload(Exhibition.photos).joinedload(ExhibitionPhoto.image).selectinload(Image.renditions),
            )
            .order_by(Exhibition.start_date.desc())
        )
        .unique()
        .scalars()
        .all()
    )

    shows: list[ExhibitionsIndexShow] = []
    for ex in exhibitions:
        category_photos: dict[str, list] = {"showcard": [], "installation": []}
        for p in ex.photos or []:
            if not p.image:
                continue
            if p.category in ("opening_reception", "in_progress"):
                continue
            category_photos.setdefault(p.category, []).append(p)

        showcard = category_photos.get("showcard", [])
        first_showcard = showcard[0] if showcard else None

        middle: list[tuple[Optional[str], Optional[str]]] = []
        for p in category_photos.get("installation", []):
            t, f = _rendition_urls(p.image, storage)
            middle.append((t, f or t))
        for a in ex.artworks or []:
            if a.images:
                t, f = _rendition_urls(a.images[0], storage)
                middle.append((t, f or t))

        import random
        for i in range(len(middle) - 1, 0, -1):
            j = random.randint(0, i)
            middle[i], middle[j] = middle[j], middle[i]

        rest = showcard[1:] if showcard else []

        gallery_images: list[ExhibitionsIndexImage] = []
        if first_showcard:
            t, f = _rendition_urls(first_showcard.image, storage)
            gallery_images.append(ExhibitionsIndexImage(thumbnail_url=t, full_url=f or t))
        for t, f in middle:
            gallery_images.append(ExhibitionsIndexImage(thumbnail_url=t, full_url=f or t))
        for p in rest:
            t, f = _rendition_urls(p.image, storage)
            gallery_images.append(ExhibitionsIndexImage(thumbnail_url=t, full_url=f or t))

        li_url = None
        if ex.listing_image:
            t, _ = _rendition_urls(ex.listing_image, storage)
            li_url = t

        shows.append(ExhibitionsIndexShow(
            slug=ex.slug,
            title=ex.title,
            start_date=ex.start_date,
            artists=[a.name for a in (ex.artists or [])],
            video_embed_url=ex.video_embed_url or "",
            listing_image_url=li_url,
            gallery=gallery_images,
        ))

    return ExhibitionsIndexPageOut(shows=shows)
