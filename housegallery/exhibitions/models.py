import datetime
import random

from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import HelpPanel
from wagtail.admin.panels import InlinePanel
from wagtail.admin.panels import MultiFieldPanel
from wagtail.admin.panels import MultipleChooserPanel
from wagtail.fields import RichTextField
from wagtail.fields import StreamField
from wagtail.images import get_image_model_string
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Orderable
from wagtail.search import index

from housegallery.artists.widgets import ArtistChooserPanel
from housegallery.artworks.widgets import ArtworkChooserPanel
from housegallery.core.blocks import BlankStreamBlock
from housegallery.core.mixins import ListingFields
from housegallery.core.mixins import Page
from housegallery.exhibitions.blocks import ExhibitionStreamBlock

from .views import ExhibitionImageChooserWidget

# Event type choices for EventPage
EVENT_TYPE_CHOICES = [
    # Exhibition Related
    ("exhibition_opening", "Exhibition Opening"),
    ("exhibition_closing", "Exhibition Closing"),
    ("gallery_tour", "Gallery Tour"),

    # Educational
    ("artist_talk", "Artist Talk"),
    ("workshop", "Workshop"),
    ("lecture", "Lecture"),
    ("critique", "Critique Session"),

    # Performance & Social
    ("performance", "Performance"),
    ("reception", "Reception"),
    ("networking", "Networking Event"),

    # Sales & Markets
    ("art_sale", "Art Sale"),
    ("art_fair", "Art Fair"),
    ("studio_sale", "Studio Sale"),

    # Residency & Community
    ("open_studio", "Open Studio"),
    ("residency_presentation", "Residency Presentation"),
    ("community_event", "Community Event"),

    # Fundraising
    ("fundraiser", "Fundraiser"),
    ("benefit", "Benefit Event"),

    # Other
    ("other", "Other"),
]







# Temporary block for migration compatibility - simple pass-through
class MultipleImagesBlock(blocks.Block):
    """Temporary block to support existing migrations."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    class Meta:
        template = "components/exhibitions/multiple_images_block.html"
        icon = "image"
        label = "Multiple Images"


class ExhibitionsIndexPage(Page, ListingFields):
    """A page listing all exhibitions."""

    body = StreamField(ExhibitionStreamBlock(), blank=True)

    template = "pages/exhibitions/exhibitions_listing.html"

    parent_page_types = [
        "home.HomePage",
        "core.BlankPage",
    ]
    subpage_types = [
        "exhibitions.ExhibitionPage",
        "exhibitions.SchedulePage",
        "core.BlankPage",
    ]

    search_fields = Page.search_fields + ListingFields.search_fields + [
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]

    promote_panels = (
        Page.promote_panels
        + ListingFields.promote_panels
    )

    def get_optimized_exhibitions(self):
        """
        Return all live ExhibitionPage objects with optimized prefetching.
        
        This method loads all data needed for the exhibitions listing page in a single
        optimized queryset, eliminating N+1 queries by prefetching:
        - Exhibition core relationships (artists, artworks)
        - All photo types with their images and renditions
        """
        from django.db.models import Prefetch

        return ExhibitionPage.objects.live().public().descendant_of(self).prefetch_related(
            # Core exhibition relationships (basic only)
            "exhibition_artists__artist",
            Prefetch("exhibition_artworks",
                queryset=ExhibitionArtwork.objects
                    .select_related("artwork")
                    .prefetch_related(
                        "artwork__artwork_images__image",
                        "artwork__artwork_images__image__renditions",
                        "artwork__artists",
                        "artwork__materials",
                    ),
            ),

            # Photo prefetches (simplified - no artwork relationships)
            Prefetch("installation_photos",
                queryset=InstallationPhoto.objects
                    .select_related("image")
                    .prefetch_related("image__renditions"),
            ),
            Prefetch("opening_reception_photos",
                queryset=OpeningReceptionPhoto.objects
                    .select_related("image")
                    .prefetch_related("image__renditions"),
            ),
            Prefetch("showcard_photos",
                queryset=ShowcardPhoto.objects
                    .select_related("image")
                    .prefetch_related("image__renditions"),
            ),
            Prefetch("in_progress_photos",
                queryset=InProgressPhoto.objects
                    .select_related("image")
                    .prefetch_related("image__renditions"),
            ),
            Prefetch("exhibition_images",
                queryset=ExhibitionImage.objects
                    .select_related("image")
                    .prefetch_related("image__renditions"),
            ),

        ).order_by("-start_date")

    def get_exhibitions(self):
        """Backwards compatibility wrapper for get_optimized_exhibitions."""
        return self.get_optimized_exhibitions()

    def get_context(self, request):
        """Add exhibitions to the context with upcoming/current/past categorization."""
        context = super().get_context(request)
        all_exhibitions = self.get_optimized_exhibitions()

        # Get today's date for comparison
        from django.utils import timezone
        today = timezone.now().date()

        # Filter exhibitions by date
        upcoming_exhibitions = []
        current_exhibitions = []
        past_exhibitions = []

        for exhibition in all_exhibitions:
            if exhibition.start_date and exhibition.start_date > today:
                upcoming_exhibitions.append(exhibition)
            elif (exhibition.start_date and exhibition.start_date <= today and
                  ((exhibition.end_date and exhibition.end_date >= today) or not exhibition.end_date)):
                current_exhibitions.append(exhibition)
            else:
                past_exhibitions.append(exhibition)

        # Paginate only past exhibitions
        paginator = Paginator(past_exhibitions, 10)  # Show 10 past exhibitions per page
        page = request.GET.get("page")

        try:
            paginated_past_exhibitions = paginator.page(page)
        except PageNotAnInteger:
            paginated_past_exhibitions = paginator.page(1)
        except EmptyPage:
            paginated_past_exhibitions = paginator.page(paginator.num_pages)

        context["upcoming_exhibitions"] = upcoming_exhibitions
        context["current_exhibitions"] = current_exhibitions
        context["past_exhibitions"] = paginated_past_exhibitions
        context["all_exhibitions"] = all_exhibitions  # Add all exhibitions for simple listing
        return context


class ExhibitionArtist(Orderable):
    """A link between an exhibition and it's main artists"""
    page = ParentalKey(
        "ExhibitionPage",
        on_delete=models.CASCADE,
        related_name="exhibition_artists",
    )
    artist = models.ForeignKey(
        "artists.Artist",
        on_delete=models.CASCADE,
        related_name="exhibition_pages",
    )

    panels = [
        ArtistChooserPanel("artist"),
    ]


class ExhibitionArtwork(Orderable):
    """A link between an exhibition and the artwork"""
    page = ParentalKey(
        "ExhibitionPage",
        on_delete=models.CASCADE,
        related_name="exhibition_artworks",
    )
    artwork = models.ForeignKey(
        "artworks.Artwork",
        on_delete=models.CASCADE,
        related_name="exhibition_pages",
    )

    panels = [
        ArtworkChooserPanel("artwork"),
    ]




class InstallationPhoto(Orderable):
    """Installation photos showing gallery setup and artwork display"""
    page = ParentalKey(
        "ExhibitionPage",
        on_delete=models.CASCADE,
        related_name="installation_photos",
    )
    image = models.ForeignKey(
        get_image_model_string(),
        on_delete=models.CASCADE,
        related_name="+",
    )
    related_artwork = models.ForeignKey(
        "artworks.Artwork",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="installation_photos",
        help_text="Automatically detected artwork relationship based on image usage",
    )

    panels = [
        FieldPanel("image", widget=ExhibitionImageChooserWidget()),
    ]

    class Meta:
        verbose_name = "Installation Photo"
        verbose_name_plural = "Installation Photos"



class OpeningReceptionPhoto(Orderable):
    """Photos from exhibition opening reception events"""
    page = ParentalKey(
        "ExhibitionPage",
        on_delete=models.CASCADE,
        related_name="opening_reception_photos",
    )
    image = models.ForeignKey(
        get_image_model_string(),
        on_delete=models.CASCADE,
        related_name="+",
    )

    panels = [
        FieldPanel("image", widget=ExhibitionImageChooserWidget()),
    ]

    class Meta:
        verbose_name = "Opening Reception Photo"
        verbose_name_plural = "Opening Reception Photos"


class ShowcardPhoto(Orderable):
    """Exhibition showcards and promotional materials"""
    page = ParentalKey(
        "ExhibitionPage",
        on_delete=models.CASCADE,
        related_name="showcard_photos",
    )
    image = models.ForeignKey(
        get_image_model_string(),
        on_delete=models.CASCADE,
        related_name="+",
    )

    panels = [
        FieldPanel("image", widget=ExhibitionImageChooserWidget()),
    ]

    class Meta:
        verbose_name = "Showcard Photo"
        verbose_name_plural = "Showcard Photos"
        ordering = ["sort_order"]


class InProgressPhoto(Orderable):
    """Behind-the-scenes photos of exhibition setup and preparation"""
    page = ParentalKey(
        "ExhibitionPage",
        on_delete=models.CASCADE,
        related_name="in_progress_photos",
    )
    image = models.ForeignKey(
        get_image_model_string(),
        on_delete=models.CASCADE,
        related_name="+",
    )

    panels = [
        FieldPanel("image", widget=ExhibitionImageChooserWidget()),
    ]

    class Meta:
        verbose_name = "In Progress Photo"
        verbose_name_plural = "In Progress Photos"


class ExhibitionImage(Orderable):
    """Through model for exhibition images with image type categorization"""
    page = ParentalKey(
        "ExhibitionPage",
        on_delete=models.CASCADE,
        related_name="exhibition_images",
    )
    image = models.ForeignKey(
        get_image_model_string(),
        on_delete=models.CASCADE,
        related_name="+",
    )
    caption = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional caption for this image",
    )
    image_type = models.CharField(
        max_length=20,
        choices=[
            ("exhibition", "Installation Photos"),
            ("opening", "Opening Reception"),
            ("showcards", "Showcards"),
            ("in_progress", "In Progress Shots"),
        ],
        default="exhibition",
        help_text="Categorize this image: Installation Photos (gallery setup), Opening Reception (event photos), Showcards (promotional materials), or In Progress Shots (behind-the-scenes)",
    )
    related_artwork = models.ForeignKey(
        "artworks.Artwork",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exhibition_images",
        help_text="Automatically detected artwork relationship based on image usage",
    )

    panels = [
        FieldPanel("image", widget=ExhibitionImageChooserWidget()),
        FieldPanel("caption"),
        FieldPanel("image_type"),
    ]

    class Meta:
        verbose_name = "Exhibition Image"
        verbose_name_plural = "Exhibition Images"





class ExhibitionPage(Page, ListingFields, ClusterableModel):
    """Individual exhibition page."""

    start_date = models.DateField("Exhibition start date",
        blank=True,
        null=True,
    )
    end_date = models.DateField("Exhibition end date",
        blank=True,
        null=True,
    )
    description = RichTextField(
        blank=True,
    )
    body = StreamField(
        ExhibitionStreamBlock(),
        blank=True,
        use_json_field=True,
        help_text="Gallery images, showcards, and other content for this exhibition",
    )
    video_embed_url = models.URLField(
        blank=True,
        null=True,
        help_text="YouTube or Vimeo URL for exhibition video content",
    )

    # Event creation fields
    create_opening_event = models.BooleanField(
        default=False,
        help_text="Check to automatically create an opening reception event for this exhibition",
    )
    auto_created_opening_event = models.ForeignKey(
        "exhibitions.EventPage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auto_created_from_exhibition",
        help_text="The opening event that was automatically created for this exhibition",
    )

    template = "pages/exhibitions/exhibition_page.html"

    parent_page_types = [
		"exhibitions.ExhibitionsIndexPage",
		"core.BlankPage",
	]
    subpage_types = [
		"core.BlankPage",
	]

    search_fields = Page.search_fields + ListingFields.search_fields + [
        index.SearchField("description"),
        index.FilterField("start_date"),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("start_date"),
            FieldPanel("end_date"),
            FieldPanel("description"),
        ], heading="Exhibition Information"),
        MultipleChooserPanel(
            "exhibition_artists",
            label="Artists",
            chooser_field_name="artist",
        ),
        MultipleChooserPanel(
            "exhibition_artworks",
            label="Artworks",
            chooser_field_name="artwork",
        ),
        FieldPanel("body"),
        MultipleChooserPanel(
            "installation_photos",
            label="Installation Photos",
            chooser_field_name="image",
        ),
        MultipleChooserPanel(
            "opening_reception_photos",
            label="Opening Reception",
            chooser_field_name="image",
        ),
        MultipleChooserPanel(
            "in_progress_photos",
            label="In Progress Shots",
            chooser_field_name="image",
        ),
        MultiFieldPanel([
            FieldPanel("video_embed_url"),
        ], heading="Video Content"),
    ]

    promote_panels = (
        Page.promote_panels
        + ListingFields.promote_panels
        + [
            MultiFieldPanel([
                FieldPanel("create_opening_event"),
            ], heading="Events"),
            MultiFieldPanel([
                MultipleChooserPanel(
                    "showcard_photos",
                    label="Showcards",
                    chooser_field_name="image",
                ),
            ], heading="Promotional Materials"),
        ]
    )

	# Artists and artworks are accessed via exhibition_artists and exhibition_artworks relationships
    # No need for properties that create additional queries

    def get_exhibition_images(self):
        """Get all installation photos (for backward compatibility)"""
        return self.installation_photos.all()

    def get_opening_images(self):
        """Get all opening reception photos"""
        return self.opening_reception_photos.all()

    def get_showcards_images(self):
        """Get all showcard photos"""
        return self.showcard_photos.all()

    def get_in_progress_images(self):
        """Get all in progress photos"""
        return self.in_progress_photos.all()

    def get_all_gallery_images(self):
        """Get all images from all typed image models with artwork data"""
        from django.core.cache import cache

        # Simple cache key based on exhibition ID and last published date
        timestamp = int(self.last_published_at.timestamp()) if self.last_published_at else 0
        cache_key = f"exhibition_images_{self.pk}_{timestamp}"
        cached_images = cache.get(cache_key)

        if cached_images is not None:
            return cached_images

        images = []

        # Helper function to process any image type
        def process_image(gallery_image, image_type):
            """Process a single image with standard renditions and metadata"""
            # Generate standard rendition URLs
            try:
                thumb_rendition = gallery_image.image.get_rendition("width-400")
                full_rendition = gallery_image.image.get_rendition("width-1200")
                thumb_url = thumb_rendition.url
                full_url = full_rendition.url

                # Generate WebP versions
                try:
                    thumb_webp = gallery_image.image.get_rendition("width-400|format-webp")
                    full_webp = gallery_image.image.get_rendition("width-1200|format-webp")
                    thumb_webp_url = thumb_webp.url
                    full_webp_url = full_webp.url
                except Exception:
                    thumb_webp_url = thumb_url
                    full_webp_url = full_url
            except Exception:
                # Fallback to original image
                thumb_url = gallery_image.image.file.url
                full_url = gallery_image.image.file.url
                thumb_webp_url = thumb_url
                full_webp_url = full_url

            # Base image data - store only serializable values for caching
            image_data = {
                "image_title": gallery_image.image.title or "",
                "caption": gallery_image.image.title or "",  # Alias for template compatibility
                "credit": gallery_image.image.credit or "",
                "type": image_type,
                "thumb_url": thumb_url,
                "full_url": full_url,
                "thumb_webp_url": thumb_webp_url,
                "full_webp_url": full_webp_url,
            }

            return image_data

        # Process each image type using prefetched data
        # Installation photos (exhibition images)
        for gallery_image in self.installation_photos.all():
            images.append(process_image(gallery_image, "exhibition"))

        # Opening reception photos
        for gallery_image in self.opening_reception_photos.all():
            images.append(process_image(gallery_image, "opening"))

        # Showcard photos
        for gallery_image in self.showcard_photos.all():
            images.append(process_image(gallery_image, "showcards"))

        # In progress photos
        for gallery_image in self.in_progress_photos.all():
            images.append(process_image(gallery_image, "in_progress"))

        # Cache the processed images for 1 hour
        cache.set(cache_key, images, 3600)

        return images

    def get_randomized_gallery_images(self, seed=None):
        """Get all gallery images in randomized order using date-based seed for daily consistency"""
        if seed is None:
            # Use current date as seed for consistent daily randomization
            seed = datetime.date.today().isoformat()

        # Get all images first
        images = self.get_all_gallery_images()

        # Create a copy and shuffle it
        randomized_images = images.copy()
        random.seed(seed)
        random.shuffle(randomized_images)

        return randomized_images

    def get_filtered_gallery_images(self, max_images=10):
        """
        Get filtered gallery images for exhibitions index page with:
        - First showcard as first item
        - Randomly mixed installation photos and artworks in middle
        - Remaining showcards as last items
        - Excludes opening reception photos and in-progress photos

        Args:
            max_images: Maximum number of images to return (default 10 for performance)
        """
        from django.core.cache import cache

        # Simple cache key based on exhibition ID, last published date, and max_images
        timestamp = int(self.last_published_at.timestamp()) if self.last_published_at else 0
        cache_key = f"exhibition_filtered_images_{self.pk}_{timestamp}_{max_images}"
        cached_images = cache.get(cache_key)

        if cached_images is not None:
            return cached_images

        images = []

        # Helper function to process any image type (reuse from get_all_gallery_images)
        def process_image(gallery_image, image_type):
            """Process a single image with standard renditions and metadata"""
            # Generate standard rendition URLs
            try:
                thumb_rendition = gallery_image.image.get_rendition("width-400")
                full_rendition = gallery_image.image.get_rendition("width-1200")
                thumb_url = thumb_rendition.url
                full_url = full_rendition.url

                # Generate WebP versions
                try:
                    thumb_webp = gallery_image.image.get_rendition("width-400|format-webp")
                    full_webp = gallery_image.image.get_rendition("width-1200|format-webp")
                    thumb_webp_url = thumb_webp.url
                    full_webp_url = full_webp.url
                except Exception:
                    thumb_webp_url = thumb_url
                    full_webp_url = full_url
            except Exception:
                # Fallback to original image
                thumb_url = gallery_image.image.file.url
                full_url = gallery_image.image.file.url
                thumb_webp_url = thumb_url
                full_webp_url = full_url

            # Base image data - store only serializable values for caching
            image_data = {
                "image_title": gallery_image.image.title or "",
                "caption": gallery_image.image.title or "",  # Alias for template compatibility
                "credit": gallery_image.image.credit or "",
                "type": image_type,
                "thumb_url": thumb_url,
                "full_url": full_url,
                "thumb_webp_url": thumb_webp_url,
                "full_webp_url": full_webp_url,
            }

            return image_data

        # Helper function to process artworks
        def process_artwork(exhibition_artwork):
            """Process a single artwork's first gallery image as a regular gallery item"""
            artwork = exhibition_artwork.artwork

            # Get first image from artwork_images relationship (Gallery Images > Images)
            first_artwork_image = artwork.artwork_images.first()
            if not first_artwork_image:
                # No gallery image available - skip this artwork
                return None

            primary_image = first_artwork_image.image

            try:
                thumb_rendition = primary_image.get_rendition("width-400")
                full_rendition = primary_image.get_rendition("width-1200")
                thumb_url = thumb_rendition.url
                full_url = full_rendition.url

                # Generate WebP versions
                try:
                    thumb_webp = primary_image.get_rendition("width-400|format-webp")
                    full_webp = primary_image.get_rendition("width-1200|format-webp")
                    thumb_webp_url = thumb_webp.url
                    full_webp_url = full_webp.url
                except Exception:
                    thumb_webp_url = thumb_url
                    full_webp_url = full_url
            except Exception:
                thumb_url = primary_image.file.url
                full_url = primary_image.file.url
                thumb_webp_url = thumb_url
                full_webp_url = full_url

            # Format materials as string (use prefetched data)
            materials_list = list(artwork.materials.all())
            materials_str = ", ".join(tag.name for tag in materials_list) if materials_list else ""

            # Get date year as string for serialization
            date_year = str(artwork.date.year) if artwork.date else ""

            # Create artwork image data - store only serializable values for caching
            artwork_image_data = {
                "image_title": primary_image.title or "",
                "caption": primary_image.title or "",  # Alias for template compatibility
                "credit": primary_image.credit or "",
                "type": "artwork",
                "thumb_url": thumb_url,
                "full_url": full_url,
                "thumb_webp_url": thumb_webp_url,
                "full_webp_url": full_webp_url,
                # Include artwork metadata for modal display (all strings for cache serialization)
                "related_artwork": {
                    "title": str(artwork) if artwork.title else "",
                    "artist_names": artwork.artist_names or "",
                    "date": {"year": date_year},  # Nested dict with year as string
                    "size": artwork.size or "",
                },
                "artwork_materials": materials_str,
            }

            return artwork_image_data

        # Get showcard photos
        showcard_photos = list(self.showcard_photos.all())

        # Add first showcard if available
        if showcard_photos:
            first_showcard = showcard_photos[0]
            images.append(process_image(first_showcard, "showcards"))

        # Early return if we've hit the limit
        if len(images) >= max_images:
            cache.set(cache_key, images[:max_images], 3600)
            return images[:max_images]

        # Collect installation photos and artworks for random mixing
        # Limit the number we process to avoid excessive rendition generation
        middle_items = []
        remaining_slots = max_images - len(images) - 1  # Reserve 1 slot for potential ending showcard

        # Add installation photos (limited)
        installation_photos = list(self.installation_photos.all()[:remaining_slots])
        for gallery_image in installation_photos:
            middle_items.append(process_image(gallery_image, "exhibition"))

        # Add artworks that have images (limited by remaining slots)
        artworks_to_check = remaining_slots - len(middle_items)
        if artworks_to_check > 0:
            for exhibition_artwork in list(self.exhibition_artworks.all()[:artworks_to_check * 2]):  # Check more in case some lack images
                if len(middle_items) >= remaining_slots:
                    break
                artwork_data = process_artwork(exhibition_artwork)
                if artwork_data:  # Only add if artwork has an image
                    middle_items.append(artwork_data)

        # Randomly shuffle the middle items (installation photos + artworks)
        random.shuffle(middle_items)
        images.extend(middle_items[:remaining_slots])

        # Add one more showcard at the end if available and we have room
        if len(showcard_photos) > 1 and len(images) < max_images:
            images.append(process_image(showcard_photos[1], "showcards"))

        # Ensure we don't exceed max_images
        images = images[:max_images]

        # Cache the processed images for 1 hour
        cache.set(cache_key, images, 3600)

        return images

    def get_current_date(self):
        """Return the current date for date comparisons."""
        from django.utils import timezone
        return timezone.now().date()

    def get_formatted_date_short(self):
        """Return start date in MM.DD.YYYY format."""
        if not self.start_date:
            return ""

        return self.start_date.strftime("%m.%d.%Y")

    def get_formatted_date_month_year(self):
        """Return start date in MM.YYYY format for exhibition context."""
        if not self.start_date:
            return ""

        return self.start_date.strftime("%m.%Y")

    def get_first_showcard_image(self):
        """Get the first showcard image for this exhibition."""
        showcard_images = self.get_showcards_images()
        if showcard_images.exists():
            return showcard_images.first().image
        return None

    def get_hero_showcard_data(self):
        """Get front and back showcard images for hero section display."""
        # Fetch showcards once and slice - avoids N+1 .count() queries
        showcards = list(self.showcard_photos.all()[:2])

        if showcards:
            first_showcard = showcards[0].image if len(showcards) > 0 else None
            second_showcard = showcards[1].image if len(showcards) > 1 else None

            return {
                'has_showcards': True,
                'front_image': first_showcard,
                'back_image': second_showcard
            }

        return {
            'has_showcards': False,
            'front_image': None,
            'back_image': None
        }

    def get_first_gallery_image(self):
        """Get the first gallery image for this exhibition."""
        gallery_images = self.get_all_gallery_images()
        if gallery_images:
            return gallery_images[0]
        return None

    def get_unified_gallery_images(self):
        """
        Get all images from all sections combined into one unified gallery structure
        for the exhibition page quickview functionality.
        
        Returns images in order:
        1. Installation photos
        2. All artwork images (grouped by artwork)  
        3. Opening reception photos
        4. In progress shots
        """
        from django.core.cache import cache

        # Simple cache key based on exhibition ID and last published date
        timestamp = int(self.last_published_at.timestamp()) if self.last_published_at else 0
        cache_key = f"exhibition_unified_images_{self.pk}_{timestamp}"
        cached_images = cache.get(cache_key)

        if cached_images is not None:
            return cached_images

        images = []

        # Helper function to process any image type (reused from existing methods)
        def process_image(gallery_image, image_type, artwork_data=None):
            """Process a single image with standard renditions and metadata"""
            # Generate standard rendition URLs
            try:
                thumb_rendition = gallery_image.image.get_rendition("width-400")
                full_rendition = gallery_image.image.get_rendition("width-1200")
                thumb_url = thumb_rendition.url
                full_url = full_rendition.url

                # Generate WebP versions
                try:
                    thumb_webp = gallery_image.image.get_rendition("width-400|format-webp")
                    full_webp = gallery_image.image.get_rendition("width-1200|format-webp")
                    thumb_webp_url = thumb_webp.url
                    full_webp_url = full_webp.url
                except Exception:
                    thumb_webp_url = thumb_url
                    full_webp_url = full_url
            except Exception:
                # Fallback to original image
                thumb_url = gallery_image.image.file.url
                full_url = gallery_image.image.file.url
                thumb_webp_url = thumb_url
                full_webp_url = full_url

            # Base image data structure - store only serializable values for caching
            image_data = {
                "image_title": gallery_image.image.title or "",
                "caption": gallery_image.image.title or "",  # Alias for template compatibility
                "credit": gallery_image.image.credit or "",
                "type": image_type,
                "thumb_url": thumb_url,
                "full_url": full_url,
                "thumb_webp_url": thumb_webp_url,
                "full_webp_url": full_webp_url,
                "exhibition_title": self.title,
                "exhibition_date": self.get_formatted_date_short(),
            }

            # Add artwork metadata if provided
            if artwork_data:
                image_data.update({
                    "related_artwork": artwork_data,
                    "artwork_materials": artwork_data.get("materials_str", ""),
                })

            return image_data

        # 1. Installation photos (exhibition images)
        for gallery_image in self.installation_photos.all():
            images.append(process_image(gallery_image, "exhibition"))

        # 2. All artwork images (grouped by artwork, all images per artwork)
        for exhibition_artwork in self.exhibition_artworks.all():
            artwork = exhibition_artwork.artwork

            # Get all artwork images, not just featured image
            artwork_images = artwork.artwork_images.all()

            if artwork_images.exists():
                # Format materials as string
                materials_str = ", ".join(tag.name for tag in artwork.materials.all()) if artwork.materials.all() else None

                # Create artwork metadata
                artwork_data = {
                    "title": artwork.title,  # Use artwork.title directly to match template
                    "artist_names": artwork.artist_names if artwork.artist_names else None,
                    "date": artwork.date.year if artwork.date else None,  # Show just the year
                    "size": artwork.size,
                    "materials_str": materials_str,
                }

                # Add all artwork images with artwork metadata
                for artwork_image in artwork_images:
                    images.append(process_image(artwork_image, "artwork", artwork_data))

        # 3. Opening reception photos
        for gallery_image in self.opening_reception_photos.all():
            images.append(process_image(gallery_image, "opening"))

        # 4. In progress photos
        for gallery_image in self.in_progress_photos.all():
            images.append(process_image(gallery_image, "in_progress"))

        # Cache the processed images for 1 hour
        cache.set(cache_key, images, 3600)

        return images

    def get_gallery_index_mapping(self):
        """
        Get mapping data for determining quickview indices for visible gallery items.
        Returns a dictionary with section indices and artwork first image indices.
        """
        unified_images = self.get_unified_gallery_images()
        mapping = {
            'installation_indices': {},
            'opening_indices': {},
            'in_progress_indices': {},
            'artwork_first_indices': {},
            'total_count': len(unified_images)
        }
        
        # Track indices for each section
        installation_counter = 0
        opening_counter = 0
        in_progress_counter = 0
        current_artwork_title = None
        
        for index, image_data in enumerate(unified_images):
            image_type = image_data.get('type')
            
            if image_type == 'exhibition':
                mapping['installation_indices'][installation_counter] = index
                installation_counter += 1
                
            elif image_type == 'opening':
                mapping['opening_indices'][opening_counter] = index
                opening_counter += 1
                
            elif image_type == 'in_progress':
                mapping['in_progress_indices'][in_progress_counter] = index
                in_progress_counter += 1
                
            elif image_type == 'artwork':
                # Track first image index for each artwork
                # Use the same title source as the template for consistency
                related_artwork = image_data.get('related_artwork', {})
                if related_artwork:
                    artwork_title = related_artwork.get('title')
                    if artwork_title and artwork_title != current_artwork_title:
                        mapping['artwork_first_indices'][artwork_title] = index
                        current_artwork_title = artwork_title
        
        return mapping



class EventArtist(Orderable):
    """
    Through model linking Events to Artists.
    Simplified relationship without roles or featured flags.
    """
    event = ParentalKey(
        "EventPage",
        related_name="event_artists",
        on_delete=models.CASCADE,
    )
    artist = models.ForeignKey(
        "artists.Artist",
        on_delete=models.CASCADE,
        help_text="Select artist from existing list",
    )

    panels = [
        ArtistChooserPanel("artist"),
    ]

    class Meta:
        unique_together = ["event", "artist"]
        verbose_name = "Event Artist"
        verbose_name_plural = "Event Artists"

    def __str__(self):
        return f"{self.artist.name}"


class EventPage(Page, ListingFields, ClusterableModel):
    """
    Individual event pages as children of SchedulePage.
    Replaces Event snippets with full page functionality.
    """

    # Event Classification
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        help_text="Type of event (opening, talk, workshop, etc.)",
    )
    tagline = models.CharField(
        max_length=255,
        blank=True,
        help_text="Short promotional tagline for listings",
    )
    related_exhibition = models.ForeignKey(
        "exhibitions.ExhibitionPage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="related_events",
        help_text="Link this event to a specific exhibition",
    )

    # Date & Time Fields (Enhanced from month/year strings)
    start_date = models.DateField(help_text="Event start date")
    end_date = models.DateField(
        blank=True,
        null=True,
        help_text="End date if multi-day event",
    )
    start_time = models.TimeField(
        blank=True,
        null=True,
        help_text="Start time (optional for all-day events)",
    )
    end_time = models.TimeField(
        blank=True,
        null=True,
        help_text="End time (optional)",
    )
    all_day = models.BooleanField(
        default=False,
        help_text="Check if this is an all-day event",
    )

    # Location System (Place integration + custom fallback)
    venue_place = models.ForeignKey(
        "places.Place",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Select from existing gallery/art spaces",
    )
    custom_venue_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Venue name if not using a Place",
    )
    custom_address = models.TextField(
        blank=True,
        help_text="Full address if not using a Place",
    )
    location_details = models.TextField(
        blank=True,
        help_text="Additional location info (room number, directions, etc.)",
    )

    # Content Fields
    description = RichTextField(
        help_text="Event description for listings and social sharing",
    )
    body = StreamField([
        ("paragraph", blocks.RichTextBlock()),
        ("image", ImageChooserBlock()),
        ("quote", blocks.BlockQuoteBlock()),
        ("html", blocks.RawHTMLBlock()),
    ], blank=True, help_text="Detailed event content")

    # Visual Assets
    featured_image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Main event image for listings and social sharing",
    )
    gallery_images = StreamField([
        ("image", ImageChooserBlock()),
    ], blank=True, help_text="Additional event images")

    # Event Management
    capacity = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Maximum attendees (optional)",
    )
    registration_required = models.BooleanField(
        default=False,
        help_text="Does this event require registration?",
    )
    registration_link = models.URLField(
        blank=True,
        help_text="Link to registration/tickets",
    )
    ticket_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Ticket price (leave blank for free events)",
    )
    contact_email = models.EmailField(
        blank=True,
        help_text="Contact for event inquiries",
    )

    # External Integration
    external_link = models.URLField(
        blank=True,
        help_text="Link to external event page, social media, etc.",
    )

    # Admin Fields
    featured_on_schedule = models.BooleanField(
        default=True,
        help_text="Feature this event prominently on schedule page",
    )

    template = "pages/exhibitions/event_page.html"

    parent_page_types = ["exhibitions.SchedulePage"]
    subpage_types = []

    search_fields = Page.search_fields + ListingFields.search_fields + [
        index.SearchField("description"),
        index.SearchField("tagline"),
        index.SearchField("body"),
        index.FilterField("event_type"),
        index.FilterField("start_date"),
    ]

    # Wagtail Configuration
    content_panels = Page.content_panels + [
        # Basic Event Info
        MultiFieldPanel([
            FieldPanel("event_type"),
            FieldPanel("tagline"),
            FieldPanel("related_exhibition"),
        ], heading="Event Classification"),

        # Scheduling
        MultiFieldPanel([
            FieldPanel("start_date"),
            FieldPanel("end_date"),
            FieldPanel("start_time"),
            FieldPanel("end_time"),
            FieldPanel("all_day"),
        ], heading="Date & Time", classname="collapsible"),

        # Location with conditional fields
        MultiFieldPanel([
            FieldPanel("venue_place"),
            HelpPanel("OR if venue not listed:"),
            FieldPanel("custom_venue_name"),
            FieldPanel("custom_address"),
            FieldPanel("location_details"),
        ], heading="Location & Venue", classname="collapsible"),

        # Content
        FieldPanel("description"),
        FieldPanel("body"),

        # Media
        MultiFieldPanel([
            FieldPanel("featured_image"),
            FieldPanel("gallery_images"),
        ], heading="Images", classname="collapsible"),

        # Related People
        InlinePanel(
            "event_artists",
            label="Related Artists",
            help_text="Add artists involved in this event",
        ),

        # Event Management
        MultiFieldPanel([
            FieldPanel("capacity"),
            FieldPanel("registration_required"),
            FieldPanel("registration_link"),
            FieldPanel("ticket_price"),
            FieldPanel("contact_email"),
        ], heading="Registration & Pricing", classname="collapsible"),

        # External Links
        FieldPanel("external_link"),

        # Display Options
        MultiFieldPanel([
            FieldPanel("featured_on_schedule"),
        ], heading="Display Options", classname="collapsible"),
    ]

    promote_panels = (
        Page.promote_panels
        + ListingFields.promote_panels
    )

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"

    @property
    def venue_name(self):
        """Returns the venue name, prioritizing Place over custom name"""
        if self.venue_place:
            return self.venue_place.title
        return self.custom_venue_name or "TBA"

    @property
    def venue_address(self):
        """Returns formatted address, prioritizing Place over custom address"""
        if self.venue_place:
            return self.venue_place.address
        return self.custom_address or ""

    @property
    def full_location_display(self):
        """Returns complete location string for display"""
        parts = []

        # Venue name
        if self.venue_name and self.venue_name != "TBA":
            parts.append(self.venue_name)

        # Address
        if self.venue_address:
            parts.append(self.venue_address)

        # Additional details
        if self.location_details:
            parts.append(self.location_details)

        return " • ".join(parts) if parts else "Location TBA"

    @property
    def is_at_gallery_space(self):
        """Returns True if event is at a tracked gallery/art space"""
        return bool(self.venue_place)

    def get_venue_maintainers(self):
        """Returns artists who maintain the venue (if Place)"""
        if self.venue_place:
            return self.venue_place.maintainers.all()
        return []

    def get_featured_artists(self):
        """Returns all artists associated with this event (simplified)"""
        return self.event_artists.all().select_related("artist")

    def get_all_related_artists(self):
        """Returns all artists associated with this event"""
        return self.event_artists.all().select_related("artist").order_by("sort_order")

    def get_related_showcard_images(self):
        """Get showcard images from related exhibition if available"""
        if not self.related_exhibition:
            return {
                "first": None,
                "last": None,
                "all": None,
                "count": 0,
            }

        showcards = self.related_exhibition.showcard_photos.all()
        if not showcards.exists():
            return {
                "first": None,
                "last": None,
                "all": None,
                "count": 0,
            }

        count = showcards.count()
        first_image = showcards.first().image if showcards.exists() else None

        # Only return last if it's different from first
        if count > 1:
            last_showcard = showcards.last()
            last_image = last_showcard.image if last_showcard != showcards.first() else None
        else:
            last_image = None

        return {
            "first": first_image,
            "last": last_image,
            "all": showcards,
            "count": count,
        }


class SchedulePage(Page, ListingFields):
    """A page showing upcoming schedule/events."""

    intro = RichTextField(
        blank=True,
        null=True,
        help_text="Introduction text for the schedule page",
    )
    body = StreamField(
        BlankStreamBlock(),
        blank=True,
        help_text="Additional content for the schedule page",
        use_json_field=True,
    )
    contact_email = models.EmailField(
        blank=True,
        null=True,
        help_text="Email address for schedule inquiries",
    )
    submission_info = RichTextField(
        blank=True,
        null=True,
        help_text="Information about submitting artwork or proposals",
    )

    template = "pages/exhibitions/schedule_page.html"

    parent_page_types = [
        "home.HomePage",
        "core.BlankPage",
    ]
    subpage_types = ["core.BlankPage", "exhibitions.EventPage"]

    search_fields = Page.search_fields + ListingFields.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body"),
        MultiFieldPanel([
            FieldPanel("contact_email"),
            FieldPanel("submission_info"),
        ], heading="Contact Information"),
    ]

    promote_panels = (
        Page.promote_panels
        + ListingFields.promote_panels
    )

    def get_context(self, request):
        """Add events to the context."""
        context = super().get_context(request)

        # Get child EventPage instances
        context["upcoming_events"] = self.get_upcoming_events()
        context["current_events"] = self.get_current_events()
        context["featured_child_events"] = self.get_featured_events()

        return context

    # Event Query Methods for child EventPage instances
    def get_upcoming_events(self):
        """Returns upcoming events, ordered by start date"""
        from django.utils import timezone
        return self.get_children().live().type(EventPage).filter(
            eventpage__start_date__gte=timezone.now().date(),
        ).specific().order_by("eventpage__start_date")

    def get_current_events(self):
        """Returns currently happening events"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.get_children().live().type(EventPage).filter(
            eventpage__start_date__lte=today,
            eventpage__end_date__gte=today,
        ).specific().order_by("eventpage__start_date")


    def get_featured_events(self):
        """Returns events marked as featured"""
        return self.get_children().live().type(EventPage).filter(
            eventpage__featured_on_schedule=True,
        ).specific().order_by("eventpage__start_date")

    def get_events_by_type(self, event_type):
        """Returns events filtered by type"""
        return self.get_children().live().type(EventPage).filter(
            eventpage__event_type=event_type,
        ).specific().order_by("eventpage__start_date")

    def get_events_by_venue(self, place):
        """Returns events at a specific venue"""
        return self.get_children().live().type(EventPage).filter(
            eventpage__venue_place=place,
        ).specific().order_by("eventpage__start_date")

    def get_events_by_month(self, year, month):
        """Returns events for a specific month"""
        return self.get_children().live().type(EventPage).filter(
            eventpage__start_date__year=year,
            eventpage__start_date__month=month,
        ).specific().order_by("eventpage__start_date")
