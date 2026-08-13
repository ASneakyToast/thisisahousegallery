"""Pydantic response schemas for the /v1 read API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, model_validator

from app.storage import get_storage


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TagOut(ORMModel):
    id: int
    name: str
    slug: str


class SocialLinkOut(BaseModel):
    platform: str = ""
    platform_name: str = ""
    url: str = ""
    handle: str = ""


class RenditionOut(ORMModel):
    filter_spec: str
    file_path: str
    width: int
    height: int
    url: str = ""

    @model_validator(mode="after")
    def _populate_url(self) -> "RenditionOut":
        if self.file_path and not self.url:
            self.url = get_storage().url(self.file_path)
        return self


class ImageOut(ORMModel):
    id: int
    title: str = ""
    alt: str = ""
    credit: str = ""
    description: str = ""
    file_path: str
    width: int = 0
    height: int = 0
    file_url: str = ""
    renditions: list[RenditionOut] = []

    @model_validator(mode="after")
    def _populate_file_url(self) -> "ImageOut":
        if self.file_path and not self.file_url:
            self.file_url = get_storage().url(self.file_path)
        return self


class ArtistOut(ORMModel):
    id: int
    name: str
    slug: str
    bio: str = ""
    website: str = ""
    email: str = ""
    birth_year: Optional[int] = None
    socials: list[dict[str, Any]] = []
    profile_image: Optional[ImageOut] = None


class ArtistDetailOut(ArtistOut):
    artworks: list["ArtworkOut"] = []


class ArtworkOut(ORMModel):
    id: int
    title: str
    slug: str
    description: str = ""
    size: str = ""
    width_inches: Optional[float] = None
    height_inches: Optional[float] = None
    depth_inches: Optional[float] = None
    date: Optional[datetime] = None
    price: str = ""
    artifacts: list[dict[str, Any]] = []
    artists: list[ArtistOut] = []
    images: list[ImageOut] = []
    tags: list[TagOut] = []
    materials: list[TagOut] = []


class ExhibitionOut(ORMModel):
    id: int
    title: str
    slug: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: str = ""
    body: list[dict[str, Any]] = []
    video_embed_url: str = ""
    listing_title: str = ""
    listing_summary: str = ""
    listing_image: Optional[ImageOut] = None
    artists: list[ArtistOut] = []
    artworks: list[ArtworkOut] = []


class ExhibitionPhotoOut(ORMModel):
    id: int
    category: str
    sort_order: int
    image: Optional[ImageOut] = None


class ExhibitionDetailOut(ExhibitionOut):
    photos: list[ExhibitionPhotoOut] = []


class SiteSettingsOut(ORMModel):
    site_title: str = ""
    tagline: str = ""
    nav: list[dict[str, Any]] = []
    contact: dict[str, Any] = {}
    socials: list[dict[str, Any]] = []


class HomeOut(ORMModel):
    intro: str = ""
    floating_images: list[ImageOut] = []


class EventOut(ORMModel):
    id: int
    title: str = ""
    slug: str = ""
    event_type: str = ""
    tagline: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    all_day: bool = False
    custom_venue_name: str = ""
    custom_address: str = ""
    location_details: str = ""
    description: str = ""
    capacity: Optional[int] = None
    registration_required: bool = False
    registration_link: str = ""
    ticket_price: str = ""
    contact_email: str = ""
    external_link: str = ""
    featured_on_schedule: bool = False
    related_exhibition: Optional[ExhibitionOut] = None
    featured_image: Optional[ImageOut] = None


ArtistDetailOut.model_rebuild()
