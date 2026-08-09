from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin, ModelView

from app.api.v1 import router as v1_router
from app.config import settings
from app.db import engine
from app.models import Artist, Artwork, Event, Exhibition, Image, Site, Tag

app = FastAPI(
    title="This is a House Gallery Headless CMS",
    version="0.2.0",
    debug=settings.debug,
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(v1_router, prefix="/v1")

# Serve locally stored media (renditions + originals) under /media
if settings.media_storage == "local":
    app.mount(
        "/media",
        StaticFiles(directory=settings.media_root, check_dir=False),
        name="media",
    )

admin = Admin(app, engine=engine)


class SiteAdmin(ModelView, model=Site):
    column_list = [Site.id, Site.slug, Site.name]


class ArtistAdmin(ModelView, model=Artist):
    column_list = [Artist.id, Artist.name, Artist.slug]


class ArtworkAdmin(ModelView, model=Artwork):
    column_list = [Artwork.id, Artwork.title, Artwork.slug]


class ExhibitionAdmin(ModelView, model=Exhibition):
    column_list = [Exhibition.id, Exhibition.title, Exhibition.slug]


class EventAdmin(ModelView, model=Event):
    column_list = [Event.id, Event.title, Event.slug, Event.event_type, Event.start_date]


class ImageAdmin(ModelView, model=Image):
    column_list = [Image.id, Image.title, Image.file_path]


class TagAdmin(ModelView, model=Tag):
    column_list = [Tag.id, Tag.name, Tag.slug]


admin.add_view(SiteAdmin)
admin.add_view(ArtistAdmin)
admin.add_view(ArtworkAdmin)
admin.add_view(ExhibitionAdmin)
admin.add_view(EventAdmin)
admin.add_view(ImageAdmin)
admin.add_view(TagAdmin)
