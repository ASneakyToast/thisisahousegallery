from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django import forms
import random
import datetime

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel

from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel, MultipleChooserPanel

from .widgets import ExhibitionImageChooserPanel
from housegallery.artworks.widgets import ArtworkChooserPanel
from housegallery.artists.widgets import ArtistChooserPanel
from wagtail.fields import StreamField, RichTextField
from wagtail.images.models import Image
from wagtail.images import get_image_model_string
from wagtail.models import Orderable
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock


from housegallery.core.mixins import Page, ListingFields
from housegallery.exhibitions.blocks import ExhibitionStreamBlock
from housegallery.core.blocks import BlankStreamBlock






# Temporary block for migration compatibility - simple pass-through
class MultipleImagesBlock(blocks.Block):
    """Temporary block to support existing migrations."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    class Meta:
        template = 'components/exhibitions/multiple_images_block.html'
        icon = 'image'
        label = 'Multiple Images'


class ExhibitionsIndexPage(Page, ListingFields):
    """A page listing all exhibitions."""

    body = StreamField(ExhibitionStreamBlock(), blank=True)

    template = 'pages/exhibitions/exhibitions_listing.html'
    
    parent_page_types = [
        'home.HomePage',
        'core.BlankPage'
    ]
    subpage_types = [
        'exhibitions.ExhibitionPage',
        'exhibitions.SchedulePage',
        'core.BlankPage'
    ]
    
    search_fields = Page.search_fields + ListingFields.search_fields + [
        index.SearchField('body'),
    ]
    
    content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]
    
    promote_panels = (
        Page.promote_panels
        + ListingFields.promote_panels
    )
    
    def get_exhibitions(self):
        """Return all live ExhibitionPage objects, ordered by start date."""
        return ExhibitionPage.objects.live().descendant_of(self).order_by('-start_date')
    
    def get_context(self, request):
        """Add exhibitions to the context with upcoming/current/past categorization."""
        context = super().get_context(request)
        all_exhibitions = self.get_exhibitions()
        
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
        page = request.GET.get('page')
        
        try:
            paginated_past_exhibitions = paginator.page(page)
        except PageNotAnInteger:
            paginated_past_exhibitions = paginator.page(1)
        except EmptyPage:
            paginated_past_exhibitions = paginator.page(paginator.num_pages)
        
        context['upcoming_exhibitions'] = upcoming_exhibitions
        context['current_exhibitions'] = current_exhibitions
        context['past_exhibitions'] = paginated_past_exhibitions
        return context


class ExhibitionArtist(Orderable):
    """A link between an exhibition and it's main artists"""
    page = ParentalKey(
        'ExhibitionPage',
        on_delete=models.CASCADE,
        related_name='exhibition_artists'
    )
    artist = models.ForeignKey(
        'artists.Artist',
        on_delete=models.CASCADE,
        related_name='exhibition_pages'
    )

    panels = [
        ArtistChooserPanel('artist'),
    ]


class ExhibitionArtwork(Orderable):
    """A link between an exhibition and the artwork"""
    page = ParentalKey(
        'ExhibitionPage',
        on_delete=models.CASCADE,
        related_name='exhibition_artworks'
    )
    artwork = models.ForeignKey(
        'artworks.Artwork',
        on_delete=models.CASCADE,
        related_name='exhibition_pages'
    )

    panels = [
        ArtworkChooserPanel('artwork'),
    ]




class ExhibitionImage(Orderable):
    """Through model for exhibition images with image type categorization"""
    page = ParentalKey(
        'ExhibitionPage',
        on_delete=models.CASCADE,
        related_name='exhibition_images'
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
    image_type = models.CharField(
        max_length=20,
        choices=[
            ('exhibition', 'Exhibition'),
            ('opening', 'Opening'),
            ('showcards', 'Showcards'),
        ],
        default='exhibition',
        help_text="Type of image - exhibition, opening event, or showcards"
    )
    related_artwork = models.ForeignKey(
        'artworks.Artwork',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exhibition_images',
        help_text="Automatically detected artwork relationship based on image usage"
    )

    panels = [
        ExhibitionImageChooserPanel('image'),
        FieldPanel('caption'),
        FieldPanel('image_type'),
    ]

    class Meta:
        verbose_name = "Exhibition Image"
        verbose_name_plural = "Exhibition Images"

    def detect_related_artwork(self):
        """
        Automatically detect artwork relationship based on image usage.
        Uses priority-based detection:
        1. Image is artwork's cover_image
        2. Image in artwork's artwork_images
        3. Image in artwork's StreamField artifacts
        """
        if not self.page or not self.image:
            return None
            
        # Get all artworks in this exhibition
        exhibition_artworks = self.page.artworks
        
        for artwork in exhibition_artworks:
                
            # Priority 1: Gallery images match
            if hasattr(artwork, 'artwork_images') and artwork.artwork_images.filter(image=self.image).exists():
                return artwork
                
            # Priority 2: StreamField artifacts (more complex)
            if hasattr(artwork, 'artifacts') and artwork.artifacts:
                for block in artwork.artifacts:
                    if hasattr(block, 'value') and hasattr(block.value, 'get') and block.value.get('image') == self.image:
                        return artwork
        
        return None

    def update_related_artwork(self):
        """Update the cached related_artwork field with detected relationship."""
        detected_artwork = self.detect_related_artwork()
        if self.related_artwork != detected_artwork:
            self.related_artwork = detected_artwork
            # Save without triggering the save hooks to avoid recursion
            super().save(update_fields=['related_artwork'])

    def save(self, *args, **kwargs):
        """Override save to automatically detect artwork relationships."""
        super().save(*args, **kwargs)
        # Update related artwork after saving (to ensure we have an ID)
        self.update_related_artwork()


class ExhibitionPage(Page, ListingFields, ClusterableModel):
    """Individual exhibition page."""

    start_date = models.DateField("Exhibition start date",
        blank=True,
        null=True
    )
    end_date = models.DateField("Exhibition end date",
        blank=True,
        null=True
    )
    description = RichTextField(
        blank=True
    )
    featured_image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    body = StreamField(
        ExhibitionStreamBlock(),
        blank=True,
        use_json_field=True,
        help_text="Gallery images, showcards, and other content for this exhibition"
    )

    template = 'pages/exhibitions/exhibition_page.html'
    
    parent_page_types = [
		'exhibitions.ExhibitionsIndexPage',
		'core.BlankPage'
	]
    subpage_types = [
		'core.BlankPage'
	]
    
    search_fields = Page.search_fields + ListingFields.search_fields + [
        index.SearchField('description'),
        index.FilterField('start_date'),
    ]
    
    content_panels = Page.content_panels + [
  	    MultiFieldPanel([
		    FieldPanel('start_date'),
		    FieldPanel('end_date'),
            FieldPanel('description'),
            FieldPanel('featured_image'),
	    ], heading="Exhibition Information"),
	    MultipleChooserPanel(
        'exhibition_artists',
        label="Artists",
        chooser_field_name="artist"
    ),
	    MultipleChooserPanel(
        'exhibition_artworks',
        label="Artworks",
        chooser_field_name="artwork"
    ),
        FieldPanel('body'),
        MultiFieldPanel([
            MultipleChooserPanel(
                'exhibition_images',
                label="Exhibition Images",
                chooser_field_name="image"
            ),
        ], heading="Images"),
    ]
    
    promote_panels = (
        Page.promote_panels
        + ListingFields.promote_panels
    )

	# Add a property to access artists easily
    @property
    def artists(self):
        return [ea.artist for ea in self.exhibition_artists.all()]

    @property
    def artworks(self):
        return [ea.artwork for ea in self.exhibition_artworks.all()]
    
    def get_exhibition_images(self):
        """Get all images of type 'exhibition'"""
        return self.exhibition_images.filter(image_type='exhibition')
    
    def get_opening_images(self):
        """Get all images of type 'opening'"""
        return self.exhibition_images.filter(image_type='opening')
    
    def get_showcards_images(self):
        """Get all images of type 'showcards'"""
        return self.exhibition_images.filter(image_type='showcards')
    
    def get_all_gallery_images(self):
        """Get all images from MultipleChooserPanel field with artwork data"""
        images = []
        
        # Process all exhibition_images
        for gallery_image in self.exhibition_images.all():
            image_data = {
                'image': gallery_image.image,
                'caption': gallery_image.caption,
                'credit': gallery_image.image.credit,
                'type': gallery_image.image_type,
                'related_artwork': gallery_image.related_artwork,
            }
            
            # Add artwork metadata if available
            if gallery_image.related_artwork:
                artwork = gallery_image.related_artwork
                image_data.update({
                    'artwork_title': artwork.title,
                    'artwork_artist': artwork.artist_names if artwork.artist_names else None,
                    'artwork_date': artwork.date.year if artwork.date else None,
                    'artwork_materials': ', '.join([tag.name for tag in artwork.materials.all()]) if hasattr(artwork, 'materials') else None,
                    'artwork_size': artwork.size if hasattr(artwork, 'size') else None,
                })
            
            images.append(image_data)
        
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
    
    def get_first_gallery_image(self):
        """Get the first gallery image for this exhibition."""
        gallery_images = self.get_all_gallery_images()
        if gallery_images:
            return gallery_images[0]
        return None


@register_snippet
class Event(models.Model):
    """
    Reusable event snippet that can be used across multiple pages.
    Events can be managed independently and referenced from schedule pages.
    """
    title = models.CharField(
        max_length=255,
        help_text="Event title"
    )
    event_type = models.CharField(
        max_length=255,
        help_text="Type of event (e.g., Exhibition, Residency, Opening)",
        blank=True
    )
    month = models.CharField(
        max_length=20,
        help_text="Month of the event (e.g., January, February)"
    )
    year = models.IntegerField(
        blank=True,
        null=True,
        help_text="Year of the event (optional)"
    )
    description = RichTextField(
        blank=True,
        help_text="Brief description of the event"
    )
    featured_image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Optional image for this event"
    )
    link = models.URLField(
        blank=True,
        help_text="Optional link to more information"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this event from listings"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', 'month', 'title']
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self):
        if self.year:
            return f"{self.title} ({self.month} {self.year})"
        return f"{self.title} ({self.month})"

    panels = [
        MultiFieldPanel([
            FieldPanel('title'),
            FieldPanel('event_type'),
        ], heading="Basic Information"),
        MultiFieldPanel([
            FieldPanel('month'),
            FieldPanel('year'),
        ], heading="Date Information"),
        FieldPanel('description'),
        FieldPanel('featured_image'),
        FieldPanel('link'),
        FieldPanel('is_active'),
    ]

    search_fields = [
        index.SearchField('title'),
        index.SearchField('event_type'),
        index.SearchField('description'),
        index.FilterField('month'),
        index.FilterField('year'),
        index.FilterField('is_active'),
    ]



class SchedulePage(Page, ListingFields):
    """A page showing upcoming schedule/events."""

    intro = RichTextField(
        blank=True,
        null=True,
        help_text="Introduction text for the schedule page"
    )
    body = StreamField(
        BlankStreamBlock(),
        blank=True,
        help_text="Additional content for the schedule page",
        use_json_field=True
    )
    # New field to select events from snippets
    featured_events = ParentalManyToManyField(
        'exhibitions.Event',
        blank=True,
        help_text="Select events to display on this schedule page"
    )
    contact_email = models.EmailField(
        blank=True,
        null=True,
        help_text="Email address for schedule inquiries"
    )
    submission_info = RichTextField(
        blank=True,
        null=True,
        help_text="Information about submitting artwork or proposals"
    )

    template = 'pages/exhibitions/schedule_page.html'

    parent_page_types = [
        'home.HomePage',
        'core.BlankPage'
    ]
    subpage_types = ['core.BlankPage']

    search_fields = Page.search_fields + ListingFields.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('featured_events', widget=forms.CheckboxSelectMultiple),
        FieldPanel('body'),
        MultiFieldPanel([
            FieldPanel('contact_email'),
            FieldPanel('submission_info'),
        ], heading="Contact Information"),
    ]

    promote_panels = (
        Page.promote_panels
        + ListingFields.promote_panels
    )

    def get_context(self, request):
        """Add events to the context."""
        context = super().get_context(request)
        
        # Get featured events from snippets (active only)
        featured_events = self.featured_events.filter(is_active=True)
        context['featured_events'] = featured_events
        
        return context