"""Public read-only /v1 API.

Serves the content a static frontend build needs. Read-only, no auth yet
(auth/tenant keying is a later phase per the design doc).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

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
    HomeOut,
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
