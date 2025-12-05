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

        This method loads all data needed for the exhibition detail page in a single
        optimized queryset, eliminating N+1 queries by prefetching:
        - Exhibition core relationships (artists, artworks)
        - All photo types with their images and renditions

        NOTE: For listing pages, use get_optimized_exhibitions_for_listing() instead
        to avoid prefetching photo types not used in the listing template.
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

    def get_optimized_exhibitions_for_listing(self):
        """
        Return exhibitions with minimal prefetching for listing pages.

        This method only prefetches what the listing template actually uses:
        - exhibition_artists (for artist names)
        - showcard_photos (for first/last showcard)
        - installation_photos (for gallery images)
        - exhibition_artworks (for artwork images in gallery)

        Saves ~6 queries compared to get_optimized_exhibitions() by NOT prefetching:
        - opening_reception_photos
        - in_progress_photos
        - exhibition_images
        """
        from django.db.models import Prefetch

        return ExhibitionPage.objects.live().public().descendant_of(self).prefetch_related(
            # Core exhibition relationships
            "exhibition_artists__artist",

            # Only showcard photos for listing (first + ending image)
            Prefetch("showcard_photos",
                queryset=ShowcardPhoto.objects
                    .select_related("image")
                    .prefetch_related("image__renditions"),
            ),

            # Installation photos for gallery
            Prefetch("installation_photos",
                queryset=InstallationPhoto.objects
                    .select_related("image")
                    .prefetch_related("image__renditions"),
            ),

            # Exhibition artworks for gallery
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
        ).order_by("-start_date")

    def get_exhibitions(self):
        """Backwards compatibility wrapper for get_optimized_exhibitions."""
        return self.get_optimized_exhibitions()

    @staticmethod
    def get_cache_version():
        """Get the current cache version for exhibitions listing.

        This version is incremented when any ExhibitionPage is published,
        automatically invalidating cached exhibition lists.
        """
        from django.core.cache import cache
        return cache.get('exhibitions_listing_version', 0)

    @staticmethod
    def invalidate_listing_cache():
        """Invalidate the exhibitions listing cache.

        Call this when any ExhibitionPage is published/unpublished.
        Increments the cache version, causing all cached listings to miss.
        """
        from django.core.cache import cache
        import time
        # Use timestamp as version for guaranteed uniqueness
        cache.set('exhibitions_listing_version', int(time.time()), None)

    def get_context(self, request):
        """Add exhibitions to the context with upcoming/current/past categorization.

        PERFORMANCE: Caches the exhibition queryset to avoid 25+ prefetch queries
        on repeat visits. Cache is invalidated via signal when any exhibition
        is published.
        """
        from django.core.cache import cache
        from django.utils import timezone

        context = super().get_context(request)

        # Build cache key using version that changes on any exhibition publish
        cache_version = self.get_cache_version()
        cache_key = f"exhibitions_listing_{self.pk}_{cache_version}"

        # Try to get cached exhibitions
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            all_exhibitions = cached_data
        else:
            # Cache miss - run the expensive prefetch query
            all_exhibitions = list(self.get_optimized_exhibitions_for_listing())
            # Cache for 1 hour (will be invalidated sooner if exhibition published)
            cache.set(cache_key, all_exhibitions, 3600)

        # Get today's date for comparison
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
        context["all_exhibitions"] = all_exhibitions
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

    @classmethod
    def get_optimized_exhibition_detail(cls, page_pk):
        """
        Return an ExhibitionPage with all relationships optimally prefetched.

        Use this method to load an exhibition for the detail page view.
        All photo types, artworks, artists, and their related images/renditions
        are loaded in a minimal number of queries.

        Usage in view or serve():
            exhibition = ExhibitionPage.get_optimized_exhibition_detail(self.pk)

        PERFORMANCE: Reduces ~60+ queries to ~8 queries by prefetching:
        - All photo types with images and renditions
        - Artworks with their images, artists, and materials
        - Exhibition artists
        """
        from django.db.models import Prefetch
        from housegallery.artworks.models import ArtworkImage

        return cls.objects.filter(pk=page_pk).prefetch_related(
            # Exhibition artists
            "exhibition_artists__artist",

            # Artworks with all their related data
            Prefetch("exhibition_artworks",
                queryset=ExhibitionArtwork.objects
                    .select_related("artwork")
                    .prefetch_related(
                        Prefetch("artwork__artwork_images",
                            queryset=ArtworkImage.objects
                                .select_related("image")
                                .prefetch_related("image__renditions"),
                        ),
                        "artwork__artists",
                        "artwork__materials",
                    ),
            ),

            # Installation photos with images and renditions
            Prefetch("installation_photos",
                queryset=InstallationPhoto.objects
                    .select_related("image")
                    .prefetch_related("image__renditions"),
            ),

            # Opening reception photos
            Prefetch("opening_reception_photos",
                queryset=OpeningReceptionPhoto.objects
                    .select_related("image")
                    .prefetch_related("image__renditions"),
            ),

            # Showcard photos
            Prefetch("showcard_photos",
                queryset=ShowcardPhoto.objects
                    .select_related("image")
                    .prefetch_related("image__renditions"),
            ),

            # In progress photos
            Prefetch("in_progress_photos",
                queryset=InProgressPhoto.objects
                    .select_related("image")
                    .prefetch_related("image__renditions"),
            ),
        ).first()

    def get_context(self, request):
        """
        Add optimized exhibition data to the context.

        PERFORMANCE: Replaces 'self' with an optimized prefetch version to ensure
        all template access to related data uses prefetched querysets.
        """
        # Get optimized version of this page with all prefetches
        optimized_page = ExhibitionPage.get_optimized_exhibition_detail(self.pk)
        if optimized_page:
            # Copy prefetched data to self so template uses it
            self._prefetched_objects_cache = getattr(optimized_page, '_prefetched_objects_cache', {})

        context = super().get_context(request)
        return context

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

    def _process_gallery_image(self, gallery_image, image_type):
        """Helper to process a gallery image into a dict with pre-computed URLs."""
        try:
            thumb_rendition = gallery_image.image.get_rendition("width-400")
            thumb_url = thumb_rendition.url
            full_url = gallery_image.image.file.url
        except Exception:
            thumb_url = gallery_image.image.file.url
            full_url = thumb_url

        return {
            "image_title": gallery_image.image.title or "",
            "credit": gallery_image.image.credit or "",
            "type": image_type,
            "thumb_url": thumb_url,
            "full_url": full_url,
        }

    def get_exhibition_images_with_urls(self):
        """Get installation photos with pre-computed URLs for templates."""
        from django.core.cache import cache
        timestamp = int(self.last_published_at.timestamp()) if self.last_published_at else 0
        cache_key = f"exhibition_install_urls_{self.pk}_{timestamp}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        images = [self._process_gallery_image(img, "exhibition") for img in self.installation_photos.all()]
        cache.set(cache_key, images, 3600)
        return images

    def get_opening_images_with_urls(self):
        """Get opening reception photos with pre-computed URLs for templates."""
        from django.core.cache import cache
        timestamp = int(self.last_published_at.timestamp()) if self.last_published_at else 0
        cache_key = f"exhibition_opening_urls_{self.pk}_{timestamp}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        images = [self._process_gallery_image(img, "opening") for img in self.opening_reception_photos.all()]
        cache.set(cache_key, images, 3600)
        return images

    def get_in_progress_images_with_urls(self):
        """Get in progress photos with pre-computed URLs for templates."""
        from django.core.cache import cache
        timestamp = int(self.last_published_at.timestamp()) if self.last_published_at else 0
        cache_key = f"exhibition_progress_urls_{self.pk}_{timestamp}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        images = [self._process_gallery_image(img, "in_progress") for img in self.in_progress_photos.all()]
        cache.set(cache_key, images, 3600)
        return images

    def get_all_gallery_images(self):
        """Get all images from all typed image models with artwork data.

        PERFORMANCE: Uses prefetched data when available. Generates only thumb
        rendition for listing performance - full size uses original file URL.
        """
        from django.core.cache import cache

        # Simple cache key based on exhibition ID and last published date
        timestamp = int(self.last_published_at.timestamp()) if self.last_published_at else 0
        cache_key = f"exhibition_images_{self.pk}_{timestamp}"
        cached_images = cache.get(cache_key)

        if cached_images is not None:
            return cached_images

        images = []

        # Helper function to get rendition URL from prefetched data or generate
        def get_rendition_url(image_obj, filter_spec):
            """Get rendition URL, checking prefetched data first."""
            try:
                renditions = list(image_obj.renditions.all())
                for rendition in renditions:
                    if filter_spec in rendition.filter_spec:
                        return rendition.url
            except Exception:
                pass

            try:
                rendition = image_obj.get_rendition(filter_spec)
                return rendition.url
            except Exception:
                return image_obj.file.url

        # Helper function to process any image type
        def process_image(gallery_image, image_type):
            """Process a single image with standard renditions and metadata"""
            image_obj = gallery_image.image

            thumb_url = get_rendition_url(image_obj, "width-400")

            # Use original file for full size - better performance
            try:
                full_url = image_obj.file.url
            except Exception:
                full_url = thumb_url

            # Base image data - store only serializable values for caching
            image_data = {
                "image_title": image_obj.title or "",
                "caption": image_obj.title or "",
                "credit": getattr(image_obj, 'credit', '') or "",
                "type": image_type,
                "thumb_url": thumb_url,
                "full_url": full_url,
                "thumb_webp_url": thumb_url,
                "full_webp_url": full_url,
            }

            return image_data

        # Process each image type using prefetched data
        # Convert to list() to use prefetched cache
        for gallery_image in list(self.installation_photos.all()):
            images.append(process_image(gallery_image, "exhibition"))

        for gallery_image in list(self.opening_reception_photos.all()):
            images.append(process_image(gallery_image, "opening"))

        for gallery_image in list(self.showcard_photos.all()):
            images.append(process_image(gallery_image, "showcards"))

        for gallery_image in list(self.in_progress_photos.all()):
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

    def get_filtered_gallery_images(self, max_images=None):
        """
        Get filtered gallery images for exhibitions index page with:
        - First showcard as first item
        - Randomly mixed installation photos and artworks in middle
        - Remaining showcards as last items
        - Excludes opening reception photos and in-progress photos

        Args:
            max_images: Maximum number of images to return (None = no limit, show all)
        """
        from django.core.cache import cache

        # Simple cache key based on exhibition ID, last published date, and max_images
        timestamp = int(self.last_published_at.timestamp()) if self.last_published_at else 0
        cache_key = f"exhibition_filtered_images_v2_{self.pk}_{timestamp}_{max_images}"
        cached_images = cache.get(cache_key)

        if cached_images is not None:
            return cached_images

        images = []

        # Helper function to get thumb URL and dimensions using prefetched renditions when available
        def get_thumb_data_from_image(image_obj):
            """Get thumbnail URL and dimensions, using prefetched renditions if available.

            PERFORMANCE: Checks prefetched renditions first to avoid DB query.
            Only calls get_rendition() if rendition not found in prefetch.

            Returns dict with 'url', 'width', 'height' keys.
            """
            # Try to find width-400 rendition in prefetched data
            try:
                renditions = list(image_obj.renditions.all())
                for rendition in renditions:
                    if 'width-400' in rendition.filter_spec:
                        return {
                            "url": rendition.url,
                            "width": rendition.width,
                            "height": rendition.height,
                        }
            except Exception:
                pass

            # Fall back to generating rendition (will check DB)
            try:
                thumb_rendition = image_obj.get_rendition("width-400")
                return {
                    "url": thumb_rendition.url,
                    "width": thumb_rendition.width,
                    "height": thumb_rendition.height,
                }
            except Exception:
                # Ultimate fallback - use original image dimensions
                return {
                    "url": image_obj.file.url,
                    "width": image_obj.width,
                    "height": image_obj.height,
                }

        # Helper function to process any image type
        def process_image(gallery_image, image_type):
            """Process a single image with standard renditions and metadata.

            Note: WebP generation is skipped on listing page for performance.
            Uses prefetched renditions when available.
            """
            image_obj = gallery_image.image
            thumb_data = get_thumb_data_from_image(image_obj)

            try:
                full_url = image_obj.file.url
            except Exception:
                full_url = thumb_data["url"]

            # Base image data - store only serializable values for caching
            image_data = {
                "image_title": image_obj.title or "",
                "caption": image_obj.title or "",
                "credit": getattr(image_obj, 'credit', '') or "",
                "type": image_type,
                "thumb_url": thumb_data["url"],
                "thumb_width": thumb_data["width"],
                "thumb_height": thumb_data["height"],
                "full_url": full_url,
                "thumb_webp_url": thumb_data["url"],
                "full_webp_url": full_url,
            }

            return image_data

        # Helper function to process artworks
        def process_artwork(exhibition_artwork):
            """Process a single artwork's first gallery image as a regular gallery item.

            Uses prefetched artwork_images and renditions when available.
            """
            artwork = exhibition_artwork.artwork

            # Use prefetched artwork_images - access as list to avoid re-query
            artwork_images = list(artwork.artwork_images.all())
            if not artwork_images:
                return None

            first_artwork_image = artwork_images[0]
            primary_image = first_artwork_image.image

            thumb_data = get_thumb_data_from_image(primary_image)

            try:
                full_url = primary_image.file.url
            except Exception:
                full_url = thumb_data["url"]

            # Format materials as string (use prefetched data)
            materials_list = list(artwork.materials.all())
            materials_str = ", ".join(tag.name for tag in materials_list) if materials_list else ""

            # Get date year as string for serialization
            date_year = str(artwork.date.year) if artwork.date else ""

            # Create artwork image data - store only serializable values for caching
            artwork_image_data = {
                "image_title": primary_image.title or "",
                "caption": primary_image.title or "",
                "credit": getattr(primary_image, 'credit', '') or "",
                "type": "artwork",
                "thumb_url": thumb_data["url"],
                "thumb_width": thumb_data["width"],
                "thumb_height": thumb_data["height"],
                "full_url": full_url,
                "thumb_webp_url": thumb_data["url"],
                "full_webp_url": full_url,
                "related_artwork": {
                    "title": str(artwork) if artwork.title else "",
                    "artist_names": getattr(artwork, 'artist_names', '') or "",
                    "date": {"year": date_year},
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

        # Collect installation photos and artworks for random mixing
        middle_items = []

        # Add all installation photos
        installation_photos = list(self.installation_photos.all())
        for gallery_image in installation_photos:
            middle_items.append(process_image(gallery_image, "exhibition"))

        # Add all artworks that have images
        for exhibition_artwork in list(self.exhibition_artworks.all()):
            artwork_data = process_artwork(exhibition_artwork)
            if artwork_data:  # Only add if artwork has an image
                middle_items.append(artwork_data)

        # Randomly shuffle the middle items (installation photos + artworks)
        random.shuffle(middle_items)
        images.extend(middle_items)

        # Add remaining showcards at the end
        for showcard in showcard_photos[1:]:
            images.append(process_image(showcard, "showcards"))

        # Apply max_images limit if specified
        if max_images is not None:
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

        PERFORMANCE: Uses prefetched data from get_optimized_exhibition_detail() to
        avoid N+1 queries. All image data is pre-loaded via select_related/prefetch_related.
        """
        from django.core.cache import cache

        # Simple cache key based on exhibition ID and last published date
        timestamp = int(self.last_published_at.timestamp()) if self.last_published_at else 0
        cache_key = f"exhibition_unified_images_{self.pk}_{timestamp}"
        cached_images = cache.get(cache_key)

        if cached_images is not None:
            return cached_images

        images = []
        exhibition_title = self.title
        exhibition_date = self.get_formatted_date_short()

        # Helper function to process any image type
        def process_image(image_obj, image_type, artwork_data=None):
            """Process a single image with standard renditions and metadata.

            Only generates thumb rendition for performance - full size uses original.
            Uses prefetched renditions when available to avoid additional queries.
            """
            # Try to use prefetched renditions first
            thumb_url = None
            prefetched_renditions = getattr(image_obj, '_prefetched_objects_cache', {}).get('renditions', [])
            if not prefetched_renditions and hasattr(image_obj, 'renditions'):
                # Check if renditions were prefetched via prefetch_related
                try:
                    prefetched_renditions = list(image_obj.renditions.all())
                except Exception:
                    prefetched_renditions = []

            # Look for existing width-400 rendition in prefetched data
            for rendition in prefetched_renditions:
                if 'width-400' in rendition.filter_spec:
                    thumb_url = rendition.url
                    break

            # Generate rendition only if not found in prefetch
            if not thumb_url:
                try:
                    thumb_rendition = image_obj.get_rendition("width-400")
                    thumb_url = thumb_rendition.url
                except Exception:
                    thumb_url = image_obj.file.url

            # Use original file for full size - loaded on demand
            try:
                full_url = image_obj.file.url
            except Exception:
                full_url = thumb_url

            # Base image data structure - store only serializable values for caching
            image_data = {
                "image_title": image_obj.title or "",
                "caption": image_obj.title or "",
                "credit": getattr(image_obj, 'credit', '') or "",
                "type": image_type,
                "thumb_url": thumb_url,
                "full_url": full_url,
                "exhibition_title": exhibition_title,
                "exhibition_date": exhibition_date,
            }

            # Add artwork metadata if provided
            if artwork_data:
                image_data.update({
                    "related_artwork": artwork_data,
                    "artwork_materials": artwork_data.get("materials_str", ""),
                })

            return image_data

        # 1. Installation photos - use prefetched data
        # Access via cached prefetch to avoid re-querying
        installation_photos = list(self.installation_photos.all())
        for gallery_image in installation_photos:
            images.append(process_image(gallery_image.image, "exhibition"))

        # 2. All artwork images (grouped by artwork, all images per artwork)
        # Use prefetched exhibition_artworks with nested artwork data
        exhibition_artworks = list(self.exhibition_artworks.all())
        for exhibition_artwork in exhibition_artworks:
            artwork = exhibition_artwork.artwork

            # Use prefetched artwork_images - no additional query
            artwork_images = list(artwork.artwork_images.all())

            if artwork_images:
                # Use prefetched materials - no additional query
                materials_list = list(artwork.materials.all())
                materials_str = ", ".join(tag.name for tag in materials_list) if materials_list else None

                # Create artwork metadata once per artwork
                artwork_data = {
                    "title": artwork.title,
                    "artist_names": getattr(artwork, 'artist_names', None),
                    "date": artwork.date.year if artwork.date else None,
                    "size": artwork.size,
                    "materials_str": materials_str,
                }

                # Process all images for this artwork
                for artwork_image in artwork_images:
                    images.append(process_image(artwork_image.image, "artwork", artwork_data))

        # 3. Opening reception photos - use prefetched data
        opening_photos = list(self.opening_reception_photos.all())
        for gallery_image in opening_photos:
            images.append(process_image(gallery_image.image, "opening"))

        # 4. In progress photos - use prefetched data
        in_progress_photos = list(self.in_progress_photos.all())
        for gallery_image in in_progress_photos:
            images.append(process_image(gallery_image.image, "in_progress"))

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
        """Get showcard images from related exhibition if available.

        PERFORMANCE: Fetches showcards once and slices in Python to avoid
        multiple .exists(), .count(), .first(), .last() queries.
        """
        if not self.related_exhibition:
            return {
                "first": None,
                "last": None,
                "all": None,
                "count": 0,
            }

        # Fetch all showcards once - avoid multiple queries
        showcards = list(self.related_exhibition.showcard_photos.all())
        count = len(showcards)

        if not showcards:
            return {
                "first": None,
                "last": None,
                "all": None,
                "count": 0,
            }

        first_image = showcards[0].image

        # Only return last if it's different from first
        last_image = showcards[-1].image if count > 1 else None

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
