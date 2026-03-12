from django.db import models
from django.utils.html import strip_tags
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import MultiFieldPanel
from wagtail.fields import StreamField
from wagtail.search import index

from housegallery.core.mixins import Page
from housegallery.kiosk.blocks import KioskBodyBlock
from housegallery.kiosk.blocks import KioskFeaturedItemsBlock
from housegallery.kiosk.blocks import KioskImageSourceBlock

CAROUSEL_TRANSITION_CHOICES = [
    ("crossfade", "Crossfade"),
    ("fade-black", "Fade to Black"),
    ("zoom-fade", "Zoom Fade"),
    ("soft-focus", "Soft Focus"),
    ("drift", "Drift (Ken Burns)"),
]


class KioskPage(Page):
    """
    Unified kiosk display page with configurable template and background.

    Supports multiple display layouts (split two-column, single center column)
    with composable content blocks (headings, QR codes, mailing list signups).
    Routed at /display/<slug>/ using the inherited Wagtail page slug.
    """

    TEMPLATE_CHOICES = [
        ("split", "Content with Featured Item(s)"),
        ("center", "Single Center Column"),
    ]

    BACKGROUND_CHOICES = [
        ("particles", "Floating Image Particles"),
        ("static_image", "Full Screen Photo"),
        ("solid_color", "Solid Color"),
    ]

    # --- Template Selection ---
    display_template = models.CharField(
        max_length=20,
        choices=TEMPLATE_CHOICES,
        default="split",
        help_text="Controls the layout and positioning of content",
    )

    # --- Featured Items (replaces display_images for split template) ---
    featured_items = StreamField(KioskFeaturedItemsBlock(), blank=True)

    # --- Display Images (kept for backward compat, will be removed later) ---
    display_images = StreamField(KioskImageSourceBlock(), blank=True)

    # --- Background ---
    background_style = models.CharField(
        max_length=20,
        choices=BACKGROUND_CHOICES,
        default="particles",
        help_text="Controls the visual background behind content",
    )
    background_gallery = StreamField(
        KioskImageSourceBlock(),
        blank=True,
        help_text="Background image(s) (for Full Screen Photo style)",
    )
    background_color = models.CharField(
        max_length=7,
        default="#111111",
        blank=True,
        help_text="Background color hex code (for Solid Color style)",
    )

    # --- Body Content (composable blocks) ---
    body = StreamField(KioskBodyBlock(), blank=True)

    # --- Particle Animation Settings ---
    max_particles = models.PositiveIntegerField(
        default=8,
        help_text="Maximum number of floating particles on screen at once",
    )
    spawn_interval_min = models.PositiveIntegerField(
        default=1500,
        help_text="Minimum milliseconds between spawning new particles",
    )
    spawn_interval_max = models.PositiveIntegerField(
        default=4000,
        help_text="Maximum milliseconds between spawning new particles",
    )

    # --- Carousel Animation Settings ---
    carousel_interval = models.PositiveIntegerField(
        default=5000,
        help_text="Milliseconds between slide transitions",
    )
    carousel_transition_duration = models.PositiveIntegerField(
        default=1200,
        help_text="Milliseconds for the transition between slides",
    )
    carousel_transition = models.CharField(
        max_length=20,
        choices=CAROUSEL_TRANSITION_CHOICES,
        default="crossfade",
        help_text="Visual effect used when transitioning between slides",
    )
    carousel_randomize = models.BooleanField(
        default=False,
        help_text="Shuffle carousel items into a random order on each page load",
    )

    parent_page_types = ["home.HomePage"]
    subpage_types = []

    TEMPLATE_MAP = {
        "split": "pages/kiosk/kiosk_split.html",
        "center": "pages/kiosk/kiosk_center.html",
    }

    def get_template(self, request=None, *args, **kwargs):
        return self.TEMPLATE_MAP.get(
            self.display_template,
            "pages/kiosk/kiosk_split.html",
        )

    def get_carousel_items(self):
        """Normalize all featured item block types into a uniform list of dicts
        for carousel rendering with lightbox data attributes."""
        items = []

        # Use featured_items if populated, fall back to display_images
        stream = self.featured_items if self.featured_items else self.display_images
        if not stream:
            return items

        for block in stream:
            if block.block_type == "artwork":
                items.extend(self._artwork_to_carousel_items(block.value))
            elif block.block_type == "exhibition":
                items.extend(self._exhibition_to_carousel_items(block.value))
            elif block.block_type == "artist":
                items.extend(self._artist_to_carousel_items(block.value))
            elif block.block_type == "all_artwork":
                items.extend(self._all_artwork_to_carousel_items(block.value))
            elif block.block_type == "single_image":
                item = self._image_to_carousel_item(block.value)
                if item:
                    items.append(item)
            elif block.block_type in ("tagged_set", "all_images"):
                items.extend(self._imageset_to_carousel_items(block))

        if self.carousel_randomize:
            import random
            random.shuffle(items)

        return items

    def _artwork_to_carousel_items(self, value):
        """Convert an artwork block to carousel items with full metadata."""
        artwork = value.get("artwork")
        if not artwork:
            return []

        items = []
        title = strip_tags(artwork.title) if artwork.title else ""
        artist_names = artwork.artist_names
        date_str = str(artwork.date.year) if artwork.date else ""
        materials = artwork.materials_list if artwork.materials_list != "-" else ""
        size = artwork.size_display

        for artwork_image in artwork.artwork_images.all():
            image_obj = artwork_image.image
            thumb_url, full_url = self._get_image_urls(image_obj)
            items.append({
                "thumb_url": thumb_url,
                "full_url": full_url,
                "caption": artwork_image.caption or title,
                "image_type": "artwork",
                "artwork_title": title,
                "artwork_artist": artist_names,
                "artwork_date": date_str,
                "artwork_materials": materials,
                "artwork_size": size,
                "exhibition_title": "",
                "exhibition_date": "",
                "image_credit": getattr(image_obj, "credit", "") or "",
            })

        return items

    def _exhibition_to_carousel_items(self, value):
        """Convert an exhibition block to carousel items, filtered by category."""
        exhibition = value.get("exhibition")
        if not exhibition:
            return []

        exhibition = exhibition.specific
        max_images = value.get("max_images")
        selected_categories = value.get("image_categories") or []

        all_images = exhibition.get_all_gallery_images()

        # Filter by selected categories if any
        if selected_categories:
            # 'artwork' category means include images with artwork metadata
            include_artwork = "artwork" in selected_categories
            photo_categories = [c for c in selected_categories if c != "artwork"]

            all_images = [
                img for img in all_images
                if img.get("type") in photo_categories
                or (include_artwork and img.get("related_artwork"))
            ]

        if max_images:
            all_images = all_images[:max_images]

        ex_title = exhibition.title
        ex_date = (
            exhibition.get_formatted_date_month_year()
            if hasattr(exhibition, "get_formatted_date_month_year")
            else ""
        )

        return [
            {
                "thumb_url": img_data.get("thumb_url", ""),
                "full_url": img_data.get("full_url", ""),
                "caption": img_data.get("caption", ex_title),
                "image_type": img_data.get("type", "exhibition"),
                "artwork_title": img_data.get("artwork_title", ""),
                "artwork_artist": img_data.get("artwork_artist", ""),
                "artwork_date": img_data.get("artwork_date", ""),
                "artwork_materials": img_data.get("artwork_materials", ""),
                "artwork_size": img_data.get("artwork_size", ""),
                "exhibition_title": ex_title,
                "exhibition_date": ex_date,
                "image_credit": img_data.get("credit", ""),
            }
            for img_data in all_images
        ]

    def _artist_to_carousel_items(self, value):
        """Convert an artist block to carousel items from their artworks."""
        artist = value.get("artist")
        if not artist:
            return []

        items = []
        for artwork in artist.artwork_list.all():
            items.extend(
                self._artwork_to_carousel_items({"artwork": artwork}),
            )

        return items

    def _all_artwork_to_carousel_items(self, value):
        """Convert an all-artwork block to carousel items from every live artwork."""
        from housegallery.artworks.models import Artwork

        artworks = Artwork.objects.filter(live=True).order_by("-date", "title")
        limit = value.get("limit")
        if limit:
            artworks = artworks[:limit]

        items = []
        for artwork in artworks:
            items.extend(self._artwork_to_carousel_items({"artwork": artwork}))
        return items

    def _image_to_carousel_item(self, value):
        """Convert a single image block to a carousel item."""
        image = value.get("image")
        if not image:
            return None

        thumb_url, full_url = self._get_image_urls(image)
        return {
            "thumb_url": thumb_url,
            "full_url": full_url,
            "caption": value.get("caption", "") or image.title or "",
            "image_type": "",
            "artwork_title": "",
            "artwork_artist": "",
            "artwork_date": "",
            "artwork_materials": "",
            "artwork_size": "",
            "exhibition_title": "",
            "exhibition_date": "",
            "image_credit": getattr(image, "credit", "") or "",
        }

    def _imageset_to_carousel_items(self, block):
        """Convert a tagged_set or all_images block to carousel items."""
        from housegallery.images.models import CustomImage

        items = []
        if block.block_type == "tagged_set":
            tag = block.value.get("tag", "")
            if not tag:
                return items
            images = CustomImage.objects.filter(tags__name__iexact=tag).distinct()
        else:
            limit = block.value.get("limit")
            images = CustomImage.objects.all()
            if limit:
                images = images[:limit]

        for image in images:
            thumb_url, full_url = self._get_image_urls(image)
            items.append({
                "thumb_url": thumb_url,
                "full_url": full_url,
                "caption": image.title or "",
                "image_type": "",
                "artwork_title": "",
                "artwork_artist": "",
                "artwork_date": "",
                "artwork_materials": "",
                "artwork_size": "",
                "exhibition_title": "",
                "exhibition_date": "",
                "image_credit": getattr(image, "credit", "") or "",
            })

        return items

    def _get_image_urls(self, image_obj):
        """Return (thumb_url, full_url) for an image object."""
        try:
            thumb = image_obj.get_rendition("width-400")
            thumb_url = thumb.url
        except (FileNotFoundError, ValueError, AttributeError):
            thumb_url = image_obj.file.url

        try:
            full_url = image_obj.file.url
        except (FileNotFoundError, ValueError, AttributeError):
            full_url = thumb_url

        return thumb_url, full_url

    search_fields = [
        *Page.search_fields,
        index.SearchField("body"),
        index.SearchField("featured_items"),
        index.SearchField("display_images"),
    ]

    content_panels = [
        *Page.content_panels,
        MultiFieldPanel([
            FieldPanel("display_template"),
            FieldPanel("featured_items"),
        ], heading="Display Template"),
        MultiFieldPanel([
            FieldPanel("background_style"),
            FieldPanel("background_gallery"),
            FieldPanel("background_color"),
        ], heading="Background"),
        FieldPanel("body"),
        MultiFieldPanel([
            FieldPanel("max_particles"),
            FieldPanel("spawn_interval_min"),
            FieldPanel("spawn_interval_max"),
        ], heading="Particle Animation Settings", classname="collapsible collapsed"),
        MultiFieldPanel([
            FieldPanel("carousel_interval"),
            FieldPanel("carousel_transition_duration"),
            FieldPanel("carousel_transition"),
            FieldPanel("carousel_randomize"),
        ], heading="Carousel Animation Settings", classname="collapsible collapsed"),
    ]

    class Meta:
        verbose_name = "Kiosk"
        verbose_name_plural = "Kiosks"
