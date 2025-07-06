from django.db import models
from django.utils import timezone

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel

from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel, MultipleChooserPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images import get_image_model_string
from wagtail.models import Orderable
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from housegallery.core.blocks.links import ListOfLinksBlock
from housegallery.core.mixins import Page, ListingFields
from housegallery.core.blocks import BlankStreamBlock
from housegallery.artists.widgets import ArtistChooserPanel
from housegallery.places.widgets import PlaceChooserPanel


class PlaceMaintainer(Orderable):
    """Through model for place-maintainer relationship with ordering."""
    place = ParentalKey(
        'Place',
        on_delete=models.CASCADE,
        related_name='place_maintainers'
    )
    artist = models.ForeignKey(
        'artists.Artist',
        on_delete=models.CASCADE,
        related_name='maintained_places'
    )

    panels = [
        ArtistChooserPanel('artist'),
    ]

    class Meta:
        verbose_name = "Place Maintainer"
        verbose_name_plural = "Place Maintainers"
        unique_together = ['place', 'artist']  # Prevent duplicate assignments


class PlaceImage(Orderable):
    """Through model for place images with captions."""
    place = ParentalKey(
        'Place',
        on_delete=models.CASCADE,
        related_name='place_images'
    )
    image = models.ForeignKey(
        get_image_model_string(),
        on_delete=models.CASCADE,
        related_name='+'
    )
    caption = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional caption for this image"
    )

    panels = [
        FieldPanel('image'),
        FieldPanel('caption'),
    ]

    class Meta:
        verbose_name = "Place Image"
        verbose_name_plural = "Place Images"


@register_snippet
class Place(ClusterableModel):
    """
    A snippet model representing an art space or venue.
    """
    title = models.CharField(
        max_length=255,
        help_text="Name of the art space or venue"
    )
    start_date = models.DateField(
        "Start date",
        blank=True,
        null=True,
        help_text="When this place opened or started operating (optional)"
    )
    end_date = models.DateField(
        "End date",
        blank=True,
        null=True,
        help_text="When this place closed (leave empty if still operating)"
    )
    address = models.TextField(
        blank=True,
        help_text="Full address of the place (optional)"
    )
    # Many-to-many field for multiple maintainers
    maintainers = ParentalManyToManyField(
        'artists.Artist',
        through='PlaceMaintainer',
        blank=True,
        related_name='places_maintained'
    )
    links = StreamField([
        ('links', ListOfLinksBlock())
    ], blank=True, help_text="Links related to this place (website, social media, etc.)")
    description = RichTextField(
        blank=True,
        help_text="Additional details about this place"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this place from listings"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        MultiFieldPanel([
            FieldPanel('title'),
        ], heading="Basic Information"),
        MultiFieldPanel([
            FieldPanel('start_date'),
            FieldPanel('end_date'),
        ], heading="Operating Period"),
        FieldPanel('address'),
        # Primary Maintainers panel
        InlinePanel('place_maintainers', label="Primary Maintainers"),
        FieldPanel('links'),
        FieldPanel('description'),
        MultiFieldPanel([
            MultipleChooserPanel(
                'place_images',
                label="Images",
                chooser_field_name="image"
            ),
        ], heading="Images"),
        FieldPanel('is_active'),
    ]

    search_fields = [
        index.SearchField('title'),
        index.SearchField('address'),
        index.SearchField('description'),
        index.SearchField('links'),
        index.FilterField('start_date'),
        index.FilterField('end_date'),
        index.FilterField('is_active'),
    ]

    def __str__(self):
        return self.title

    @property
    def is_currently_operating(self):
        """Check if the place is currently operating."""
        today = timezone.now().date()
        
        # If no start date is specified, consider it operating if no end date
        if not self.start_date:
            return not self.end_date or self.end_date >= today
            
        # If we have a start date, check normal operating logic
        if self.end_date:
            return self.start_date <= today <= self.end_date
        return self.start_date <= today

    @property
    def operating_period(self):
        """Return a formatted string of the operating period."""
        if not self.start_date and not self.end_date:
            return "Unknown period"
        elif not self.start_date and self.end_date:
            return f"Until {self.end_date.year}"
        elif self.start_date and self.end_date:
            return f"{self.start_date.year} - {self.end_date.year}"
        elif self.start_date and not self.end_date:
            return f"{self.start_date.year} - present"
        else:
            return "Unknown period"

    def get_first_image(self):
        """Get the first image for this place."""
        if self.place_images.exists():
            return self.place_images.first().image
        return None

    @property
    def maintainer_names(self):
        """Return comma-separated list of maintainer names"""
        return ", ".join([maintainer.artist.name for maintainer in self.place_maintainers.all()])

    def get_maintainers(self):
        """Return all maintainers for this place"""
        return [maintainer.artist for maintainer in self.place_maintainers.all()]

    class Meta:
        verbose_name = "Place"
        verbose_name_plural = "Places"
        ordering = ['-start_date', 'title']  # NULL start_dates will appear last


class PlacesIndexPagePlace(Orderable):
    """Through model for featured places on PlacesIndexPage with ordering."""
    page = ParentalKey(
        'PlacesIndexPage',
        on_delete=models.CASCADE,
        related_name='featured_places'
    )
    place = models.ForeignKey(
        'Place',
        on_delete=models.CASCADE,
        related_name='featured_on_pages'
    )

    panels = [
        PlaceChooserPanel('place'),
    ]

    class Meta:
        verbose_name = "Featured Place"
        verbose_name_plural = "Featured Places"
        unique_together = ['page', 'place']  # Prevent duplicate place assignments


class PlacesIndexPage(Page, ListingFields, ClusterableModel):
    """A page listing all places (art spaces and venues)."""

    intro = RichTextField(
        blank=True,
        help_text="Optional introduction text for the places listing page"
    )
    body = StreamField(
        BlankStreamBlock(),
        blank=True,
        help_text="Additional content for the places page"
    )

    template = 'pages/places/places_listing.html'
    
    parent_page_types = [
        'home.HomePage',
        'core.BlankPage'
    ]
    subpage_types = [
        'core.BlankPage'
    ]
    
    search_fields = Page.search_fields + ListingFields.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]
    
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('body'),
        MultiFieldPanel([
            MultipleChooserPanel(
                'featured_places',
                label="Featured Places",
                chooser_field_name="place"
            ),
        ], heading="Featured Places"),
    ]
    
    promote_panels = (
        Page.promote_panels
        + ListingFields.promote_panels
    )
    
    def get_places(self):
        """Return all active places, ordered by start date (most recent first)."""
        return Place.objects.filter(is_active=True).prefetch_related('place_images__image').order_by('-start_date', 'title')
    
    def get_featured_places(self):
        """Return featured places in the order specified by the editor."""
        return [fp.place for fp in self.featured_places.select_related('place').prefetch_related('place__place_images__image').all()]
    
    def get_all_featured_place_images(self):
        """Return all images from featured places for the image pool gallery."""
        featured_places = self.get_featured_places()
        if not featured_places:
            return []
        
        images = []
        for place in featured_places:
            # Use select_related to optimize image queries
            place_images = place.place_images.select_related('image').all()
            for place_image in place_images:
                if place_image.image:  # Ensure image exists
                    images.append({
                        'image': place_image.image,
                        'caption': place_image.caption,
                        'place': place,
                        'place_id': place.id,
                    })
        return images

    def get_context(self, request):
        """Add places to the context."""
        context = super().get_context(request)
        
        # If featured places are specified, use those; otherwise show all places
        featured_places = self.get_featured_places()
        if featured_places:
            context['places'] = featured_places
            context['showing_featured'] = True
            context['all_place_images'] = self.get_all_featured_place_images()
        else:
            context['places'] = self.get_places()
            context['showing_featured'] = False
            # For non-featured view, collect images from all active places
            images = []
            for place in context['places']:
                place_images = place.place_images.select_related('image').all()
                for place_image in place_images:
                    if place_image.image:  # Ensure image exists
                        images.append({
                            'image': place_image.image,
                            'caption': place_image.caption,
                            'place': place,
                            'place_id': place.id,
                        })
            context['all_place_images'] = images
            
        return context