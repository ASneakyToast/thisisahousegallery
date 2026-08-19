"""SQLAlchemy ORM models for the This is a House Gallery headless CMS.

Ported from housegallery-go. Every content table carries a nullable, indexed
`tenant_id` column (multi-tenant seam, per design decision Q1) which is unused
in single-tenant mode.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def default_now() -> datetime:
    return datetime.utcnow()


# ---------------------------------------------------------------------------
# Tenant / site
# ---------------------------------------------------------------------------
class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    settings: Mapped[Optional["SiteSettings"]] = relationship(
        back_populates="site", uselist=False
    )


class SiteSettings(Base):
    __tablename__ = "site_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    site_id: Mapped[int] = mapped_column(
        ForeignKey("sites.id", ondelete="CASCADE"), nullable=False
    )
    site_title: Mapped[str] = mapped_column(String(200), default="")
    tagline: Mapped[str] = mapped_column(Text, default="")
    nav: Mapped[list] = mapped_column(JSON, default=list)
    contact: Mapped[dict] = mapped_column(JSON, default=dict)
    socials: Mapped[list] = mapped_column(JSON, default=list)

    site: Mapped[Site] = relationship(back_populates="settings")


# ---------------------------------------------------------------------------
# Homepage hero (intro + floating images)
# ---------------------------------------------------------------------------
class HomePage(Base):
    """Homepage hero content (intro + floating images).

    Mirrors the home_homepage body's hero_section block.
    floating_image_ids is an ordered list of Image ids to drift behind the
    hero intro; editors can reorder/swap them without a code change.
    """

    __tablename__ = "home_page"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    site_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sites.id", ondelete="CASCADE"), nullable=True
    )
    intro: Mapped[str] = mapped_column(Text, default="")
    floating_image_ids: Mapped[list] = mapped_column(JSON, default=list)


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------
class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# Images + renditions
# ---------------------------------------------------------------------------
class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    alt: Mapped[str] = mapped_column(Text, default="")
    credit: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=default_now
    )

    renditions: Mapped[list["Rendition"]] = relationship(
        back_populates="image", cascade="all, delete-orphan"
    )


class Rendition(Base):
    __tablename__ = "renditions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    image_id: Mapped[int] = mapped_column(
        ForeignKey("images.id", ondelete="CASCADE"), nullable=False
    )
    filter_spec: Mapped[str] = mapped_column(String(100), default="")
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    image: Mapped[Image] = relationship(back_populates="renditions")


# ---------------------------------------------------------------------------
# Artists
# ---------------------------------------------------------------------------
class Artist(Base):
    __tablename__ = "artists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    bio: Mapped[str] = mapped_column(Text, default="")
    profile_image_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("images.id"), nullable=True
    )
    website: Mapped[str] = mapped_column(String(500), default="")
    email: Mapped[str] = mapped_column(String(320), default="")
    birth_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    socials: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=default_now
    )

    profile_image: Mapped[Optional[Image]] = relationship(foreign_keys=[profile_image_id])

    artworks: Mapped[list["Artwork"]] = relationship(
        secondary="artwork_artists", back_populates="artists"
    )


# ---------------------------------------------------------------------------
# Artworks
# ---------------------------------------------------------------------------
class Artwork(Base):
    __tablename__ = "artworks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    size: Mapped[str] = mapped_column(String(100), default="")
    width_inches: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    height_inches: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    depth_inches: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    price: Mapped[str] = mapped_column(String(100), default="")
    artifacts: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=default_now
    )

    artists: Mapped[list[Artist]] = relationship(
        secondary="artwork_artists", back_populates="artworks"
    )
    images: Mapped[list[Image]] = relationship(secondary="artwork_images")
    tags: Mapped[list[Tag]] = relationship(secondary="artwork_tags")
    exhibitions: Mapped[list["Exhibition"]] = relationship(
        secondary="exhibition_artworks", back_populates="artworks"
    )

    @property
    def materials(self) -> list[Tag]:
        """Materials are stored as tags (the source artwork had only a
        ClusterTaggableManager 'materials' field, no separate descriptive
        tags). Expose the same relationship under 'materials' so the read API
        and frontend can render them meaningfully."""
        return self.tags


# --- through tables ---
class ArtworkArtist(Base):
    __tablename__ = "artwork_artists"
    __table_args__ = (Index("ix_artwork_artists_artwork_id", "artwork_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artwork_id: Mapped[int] = mapped_column(
        ForeignKey("artworks.id", ondelete="CASCADE"), nullable=False
    )
    artist_id: Mapped[int] = mapped_column(
        ForeignKey("artists.id", ondelete="CASCADE"), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ArtworkImage(Base):
    __tablename__ = "artwork_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artwork_id: Mapped[int] = mapped_column(
        ForeignKey("artworks.id", ondelete="CASCADE"), nullable=False
    )
    image_id: Mapped[int] = mapped_column(
        ForeignKey("images.id", ondelete="CASCADE"), nullable=False
    )
    caption: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ArtworkTag(Base):
    __tablename__ = "artwork_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artwork_id: Mapped[int] = mapped_column(
        ForeignKey("artworks.id", ondelete="CASCADE"), nullable=False
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


# ---------------------------------------------------------------------------
# Exhibition photo categories
# ---------------------------------------------------------------------------
class ExhibitionPhoto(Base):
    __tablename__ = "exhibition_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exhibition_id: Mapped[int] = mapped_column(
        ForeignKey("exhibitions.id", ondelete="CASCADE"), nullable=False
    )
    image_id: Mapped[int] = mapped_column(
        ForeignKey("images.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(
        String(40), default="installation"
    )  # installation|opening_reception|showcard|in_progress
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    image: Mapped[Image] = relationship()


# ---------------------------------------------------------------------------
# Exhibitions
# ---------------------------------------------------------------------------
class Exhibition(Base):
    __tablename__ = "exhibitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    body: Mapped[list] = mapped_column(JSON, default=list)
    video_embed_url: Mapped[str] = mapped_column(String(500), default="")
    listing_title: Mapped[str] = mapped_column(String(200), default="")
    listing_summary: Mapped[str] = mapped_column(Text, default="")
    listing_image_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("images.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=default_now
    )

    listing_image: Mapped[Optional[Image]] = relationship(foreign_keys=[listing_image_id])

    artists: Mapped[list[Artist]] = relationship(secondary="exhibition_artists")
    artworks: Mapped[list[Artwork]] = relationship(secondary="exhibition_artworks")
    photos: Mapped[list[ExhibitionPhoto]] = relationship(
            back_populates="exhibition", cascade="all, delete-orphan",
            order_by="ExhibitionPhoto.sort_order",
        )


class ExhibitionArtist(Base):
    __tablename__ = "exhibition_artists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exhibition_id: Mapped[int] = mapped_column(
        ForeignKey("exhibitions.id", ondelete="CASCADE"), nullable=False
    )
    artist_id: Mapped[int] = mapped_column(
        ForeignKey("artists.id", ondelete="CASCADE"), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ExhibitionArtwork(Base):
    __tablename__ = "exhibition_artworks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exhibition_id: Mapped[int] = mapped_column(
        ForeignKey("exhibitions.id", ondelete="CASCADE"), nullable=False
    )
    artwork_id: Mapped[int] = mapped_column(
        ForeignKey("artworks.id", ondelete="CASCADE"), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


# ---------------------------------------------------------------------------
# Events (schedule — openings, talks, workshops, etc.)
# ---------------------------------------------------------------------------
class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), default="")
    tagline: Mapped[str] = mapped_column(String(255), default="")

    related_exhibition_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("exhibitions.id"), nullable=True
    )
    related_exhibition: Mapped[Optional[Exhibition]] = relationship(
        foreign_keys=[related_exhibition_id]
    )

    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    all_day: Mapped[bool] = mapped_column(default=False)

    custom_venue_name: Mapped[str] = mapped_column(String(255), default="")
    custom_address: Mapped[str] = mapped_column(Text, default="")
    location_details: Mapped[str] = mapped_column(Text, default="")

    description: Mapped[str] = mapped_column(Text, default="")
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    registration_required: Mapped[bool] = mapped_column(default=False)
    registration_link: Mapped[str] = mapped_column(String(500), default="")
    ticket_price: Mapped[str] = mapped_column(String(100), default="")
    contact_email: Mapped[str] = mapped_column(String(320), default="")
    external_link: Mapped[str] = mapped_column(String(500), default="")
    featured_on_schedule: Mapped[bool] = mapped_column(default=False)

    featured_image_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("images.id"), nullable=True
    )
    featured_image: Mapped[Optional[Image]] = relationship(
        foreign_keys=[featured_image_id]
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=default_now
    )


# Fwd ref for ExhibitionPhoto relationship
ExhibitionPhoto.exhibition = relationship(
    "Exhibition", back_populates="photos"
)
