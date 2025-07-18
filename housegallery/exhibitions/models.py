from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django import forms
import random
import datetime

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel

from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel, MultipleChooserPanel, HelpPanel
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.embeds.models import Embed
from wagtail.embeds import embeds

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

# Event type choices for EventPage
EVENT_TYPE_CHOICES = [
    # Exhibition Related
    ('exhibition_opening', 'Exhibition Opening'),
    ('exhibition_closing', 'Exhibition Closing'),
    ('gallery_tour', 'Gallery Tour'),
    
    # Educational
    ('artist_talk', 'Artist Talk'),
    ('workshop', 'Workshop'),
    ('lecture', 'Lecture'),
    ('critique', 'Critique Session'),
    
    # Performance & Social
    ('performance', 'Performance'),
    ('reception', 'Reception'),
    ('networking', 'Networking Event'),
    
    # Sales & Markets
    ('art_sale', 'Art Sale'),
    ('art_fair', 'Art Fair'),
    ('studio_sale', 'Studio Sale'),
    
    # Residency & Community
    ('open_studio', 'Open Studio'),
    ('residency_presentation', 'Residency Presentation'),
    ('community_event', 'Community Event'),
    
    # Fundraising
    ('fundraiser', 'Fundraiser'),
    ('benefit', 'Benefit Event'),
    
    # Other
    ('other', 'Other'),
]

# Artist role choices for EventArtist relationship
ARTIST_ROLE_CHOICES = [
    ('organizer', 'Event Organizer'),
    ('performer', 'Performer'),
    ('speaker', 'Speaker'),
    ('teacher', 'Workshop Teacher'),
    ('participant', 'Participant'),
    ('featured', 'Featured Artist'),
    ('curator', 'Curator'),
    ('host', 'Host'),
    ('moderator', 'Moderator'),
    ('other', 'Other'),
]






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




class InstallationPhoto(Orderable):
    """Installation photos showing gallery setup and artwork display"""
    page = ParentalKey(
        'ExhibitionPage',
        on_delete=models.CASCADE,
        related_name='installation_photos'
    )
    image = models.ForeignKey(
        get_image_model_string(),
        on_delete=models.CASCADE,
        related_name='+'
    )
    related_artwork = models.ForeignKey(
        'artworks.Artwork',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='installation_photos',
        help_text="Automatically detected artwork relationship based on image usage"
    )

    panels = [
        ExhibitionImageChooserPanel('image'),
    ]

    class Meta:
        verbose_name = "Installation Photo"
        verbose_name_plural = "Installation Photos"

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


class OpeningReceptionPhoto(Orderable):
    """Photos from exhibition opening reception events"""
    page = ParentalKey(
        'ExhibitionPage',
        on_delete=models.CASCADE,
        related_name='opening_reception_photos'
    )
    image = models.ForeignKey(
        get_image_model_string(),
        on_delete=models.CASCADE,
        related_name='+'
    )

    panels = [
        ExhibitionImageChooserPanel('image'),
    ]

    class Meta:
        verbose_name = "Opening Reception Photo"
        verbose_name_plural = "Opening Reception Photos"


class ShowcardPhoto(Orderable):
    """Exhibition showcards and promotional materials"""
    page = ParentalKey(
        'ExhibitionPage',
        on_delete=models.CASCADE,
        related_name='showcard_photos'
    )
    image = models.ForeignKey(
        get_image_model_string(),
        on_delete=models.CASCADE,
        related_name='+'
    )

    panels = [
        ExhibitionImageChooserPanel('image'),
    ]

    class Meta:
        verbose_name = "Showcard Photo"
        verbose_name_plural = "Showcard Photos"


class InProgressPhoto(Orderable):
    """Behind-the-scenes photos of exhibition setup and preparation"""
    page = ParentalKey(
        'ExhibitionPage',
        on_delete=models.CASCADE,
        related_name='in_progress_photos'
    )
    image = models.ForeignKey(
        get_image_model_string(),
        on_delete=models.CASCADE,
        related_name='+'
    )

    panels = [
        ExhibitionImageChooserPanel('image'),
    ]

    class Meta:
        verbose_name = "In Progress Photo"
        verbose_name_plural = "In Progress Photos"


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
            ('exhibition', 'Installation Photos'),
            ('opening', 'Opening Reception'),
            ('showcards', 'Showcards'),
            ('in_progress', 'In Progress Shots'),
        ],
        default='exhibition',
        help_text="Categorize this image: Installation Photos (gallery setup), Opening Reception (event photos), Showcards (promotional materials), or In Progress Shots (behind-the-scenes)"
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
    body = StreamField(
        ExhibitionStreamBlock(),
        blank=True,
        use_json_field=True,
        help_text="Gallery images, showcards, and other content for this exhibition"
    )
    video_embed_url = models.URLField(
        blank=True,
        null=True,
        help_text="YouTube or Vimeo URL for exhibition video content"
    )
    
    # Event creation fields
    create_opening_event = models.BooleanField(
        default=False,
        help_text="Check to automatically create an opening reception event for this exhibition"
    )
    auto_created_opening_event = models.ForeignKey(
        'exhibitions.EventPage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='auto_created_from_exhibition',
        help_text="The opening event that was automatically created for this exhibition"
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
        MultipleChooserPanel(
            'installation_photos',
            label="Installation Photos",
            chooser_field_name="image"
        ),
        MultipleChooserPanel(
            'opening_reception_photos',
            label="Opening Reception",
            chooser_field_name="image"
        ),
        MultipleChooserPanel(
            'in_progress_photos',
            label="In Progress Shots",
            chooser_field_name="image"
        ),
        MultiFieldPanel([
            FieldPanel('video_embed_url'),
        ], heading="Video Content"),
    ]
    
    promote_panels = (
        Page.promote_panels
        + ListingFields.promote_panels
        + [
            MultiFieldPanel([
                FieldPanel('create_opening_event'),
            ], heading="Events"),
            MultiFieldPanel([
                MultipleChooserPanel(
                    'showcard_photos',
                    label="Showcards",
                    chooser_field_name="image"
                ),
            ], heading="Promotional Materials"),
        ]
    )

	# Add a property to access artists easily
    @property
    def artists(self):
        return [ea.artist for ea in self.exhibition_artists.all()]

    @property
    def artworks(self):
        return [ea.artwork for ea in self.exhibition_artworks.all()]
    
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
        """Get all images from all image types with artwork data"""
        images = []
        
        # Process installation photos
        for gallery_image in self.installation_photos.all():
            image_data = {
                'image': gallery_image.image,
                'credit': gallery_image.image.credit,
                'type': 'exhibition',  # for backward compatibility
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
        
        # Process opening reception photos
        for gallery_image in self.opening_reception_photos.all():
            image_data = {
                'image': gallery_image.image,
                'credit': gallery_image.image.credit,
                'type': 'opening',
                'related_artwork': None,
            }
            images.append(image_data)
        
        # Process showcard photos
        for gallery_image in self.showcard_photos.all():
            image_data = {
                'image': gallery_image.image,
                'credit': gallery_image.image.credit,
                'type': 'showcards',
                'related_artwork': None,
            }
            images.append(image_data)
        
        # Process in progress photos
        for gallery_image in self.in_progress_photos.all():
            image_data = {
                'image': gallery_image.image,
                'credit': gallery_image.image.credit,
                'type': 'in_progress',
                'related_artwork': None,
            }
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



class EventArtist(Orderable):
    """
    Through model linking Events to Artists with roles.
    Allows multiple artists per event with different responsibilities.
    """
    event = ParentalKey(
        'EventPage',
        related_name='event_artists',
        on_delete=models.CASCADE
    )
    artist = models.ForeignKey(
        'artists.Artist',
        on_delete=models.CASCADE,
        help_text="Select artist from existing list"
    )
    role = models.CharField(
        max_length=50,
        choices=ARTIST_ROLE_CHOICES,
        default='participant',
        help_text="Artist's role in this event"
    )
    bio_override = models.TextField(
        blank=True,
        help_text="Custom bio for this event (optional, uses artist bio if blank)"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Feature this artist prominently for this event"
    )
    
    panels = [
        ArtistChooserPanel('artist'),
        FieldPanel('role'),
        FieldPanel('bio_override'),
        FieldPanel('is_featured'),
    ]
    
    class Meta:
        unique_together = ['event', 'artist', 'role']
        verbose_name = "Event Artist"
        verbose_name_plural = "Event Artists"
    
    def __str__(self):
        return f"{self.artist.name} - {self.get_role_display()}"


class EventPage(Page, ListingFields, ClusterableModel):
    """
    Individual event pages as children of SchedulePage.
    Replaces Event snippets with full page functionality.
    """
    
    # Event Classification
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        help_text="Type of event (opening, talk, workshop, etc.)"
    )
    tagline = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Short promotional tagline for listings"
    )
    related_exhibition = models.ForeignKey(
        'exhibitions.ExhibitionPage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_events',
        help_text="Link this event to a specific exhibition"
    )
    
    # Date & Time Fields (Enhanced from month/year strings)
    start_date = models.DateField(help_text="Event start date")
    end_date = models.DateField(
        blank=True, 
        null=True,
        help_text="End date if multi-day event"
    )
    start_time = models.TimeField(
        blank=True, 
        null=True,
        help_text="Start time (optional for all-day events)"
    )
    end_time = models.TimeField(
        blank=True, 
        null=True,
        help_text="End time (optional)"
    )
    all_day = models.BooleanField(
        default=False,
        help_text="Check if this is an all-day event"
    )
    
    # Location System (Place integration + custom fallback)
    venue_place = models.ForeignKey(
        'places.Place',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Select from existing gallery/art spaces"
    )
    custom_venue_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Venue name if not using a Place"
    )
    custom_address = models.TextField(
        blank=True,
        help_text="Full address if not using a Place"
    )
    location_details = models.TextField(
        blank=True,
        help_text="Additional location info (room number, directions, etc.)"
    )
    
    # Content Fields
    description = RichTextField(
        help_text="Event description for listings and social sharing"
    )
    body = StreamField([
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('quote', blocks.BlockQuoteBlock()),
        ('html', blocks.RawHTMLBlock()),
    ], blank=True, help_text="Detailed event content")
    
    # Visual Assets
    featured_image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Main event image for listings and social sharing"
    )
    gallery_images = StreamField([
        ('image', ImageChooserBlock()),
    ], blank=True, help_text="Additional event images")
    
    # Event Management
    capacity = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Maximum attendees (optional)"
    )
    registration_required = models.BooleanField(
        default=False,
        help_text="Does this event require registration?"
    )
    registration_link = models.URLField(
        blank=True,
        help_text="Link to registration/tickets"
    )
    ticket_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Ticket price (leave blank for free events)"
    )
    contact_email = models.EmailField(
        blank=True,
        help_text="Contact for event inquiries"
    )
    
    # External Integration
    external_link = models.URLField(
        blank=True,
        help_text="Link to external event page, social media, etc."
    )
    
    # Admin Fields
    featured_on_schedule = models.BooleanField(
        default=True,
        help_text="Feature this event prominently on schedule page"
    )
    
    template = 'pages/exhibitions/event_page.html'
    
    parent_page_types = ['exhibitions.SchedulePage']
    subpage_types = []
    
    search_fields = Page.search_fields + ListingFields.search_fields + [
        index.SearchField('description'),
        index.SearchField('tagline'),
        index.SearchField('body'),
        index.FilterField('event_type'),
        index.FilterField('start_date'),
    ]
    
    # Wagtail Configuration
    content_panels = Page.content_panels + [
        # Basic Event Info
        MultiFieldPanel([
            FieldPanel('event_type'),
            FieldPanel('tagline'),
            FieldPanel('related_exhibition'),
        ], heading="Event Classification"),
        
        # Scheduling
        MultiFieldPanel([
            FieldPanel('start_date'),
            FieldPanel('end_date'),
            FieldPanel('start_time'),
            FieldPanel('end_time'),
            FieldPanel('all_day'),
        ], heading="Date & Time", classname="collapsible"),
        
        # Location with conditional fields
        MultiFieldPanel([
            FieldPanel('venue_place'),
            HelpPanel("OR if venue not listed:"),
            FieldPanel('custom_venue_name'),
            FieldPanel('custom_address'),
            FieldPanel('location_details'),
        ], heading="Location & Venue", classname="collapsible"),
        
        # Content
        FieldPanel('description'),
        FieldPanel('body'),
        
        # Media
        MultiFieldPanel([
            FieldPanel('featured_image'),
            FieldPanel('gallery_images'),
        ], heading="Images", classname="collapsible"),
        
        # Related People
        InlinePanel(
            'event_artists',
            label="Related Artists",
            help_text="Add artists involved in this event",
        ),
        
        # Event Management
        MultiFieldPanel([
            FieldPanel('capacity'),
            FieldPanel('registration_required'),
            FieldPanel('registration_link'),
            FieldPanel('ticket_price'),
            FieldPanel('contact_email'),
        ], heading="Registration & Pricing", classname="collapsible"),
        
        # External Links
        FieldPanel('external_link'),
        
        # Display Options
        MultiFieldPanel([
            FieldPanel('featured_on_schedule'),
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
        """Returns artists marked as featured for this event"""
        return self.event_artists.filter(is_featured=True).select_related('artist')
    
    def get_organizers(self):
        """Returns event organizers"""
        return self.event_artists.filter(role='organizer').select_related('artist')
    
    def get_performers(self):
        """Returns performers/speakers"""
        return self.event_artists.filter(
            role__in=['performer', 'speaker', 'teacher']
        ).select_related('artist')
    
    def get_all_related_artists(self):
        """Returns all artists associated with this event"""
        return self.event_artists.all().select_related('artist').order_by('sort_order')


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
    subpage_types = ['core.BlankPage', 'exhibitions.EventPage']

    search_fields = Page.search_fields + ListingFields.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
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
        
        # Get child EventPage instances
        context['upcoming_events'] = self.get_upcoming_events()
        context['current_events'] = self.get_current_events()
        context['past_events'] = self.get_past_events()
        context['featured_child_events'] = self.get_featured_events()
        
        return context
    
    # Event Query Methods for child EventPage instances
    def get_upcoming_events(self):
        """Returns upcoming events, ordered by start date"""
        from django.utils import timezone
        return self.get_children().live().type(EventPage).filter(
            eventpage__start_date__gte=timezone.now().date()
        ).order_by('eventpage__start_date')
    
    def get_current_events(self):
        """Returns currently happening events"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.get_children().live().type(EventPage).filter(
            eventpage__start_date__lte=today,
            eventpage__end_date__gte=today
        ).order_by('eventpage__start_date')
    
    def get_past_events(self):
        """Returns past events, ordered by most recent first"""
        from django.utils import timezone
        from django.db.models import Q
        return self.get_children().live().type(EventPage).filter(
            Q(eventpage__end_date__lt=timezone.now().date()) |
            Q(eventpage__end_date__isnull=True, eventpage__start_date__lt=timezone.now().date())
        ).order_by('-eventpage__start_date')
    
    def get_featured_events(self):
        """Returns events marked as featured"""
        return self.get_children().live().type(EventPage).filter(
            eventpage__featured_on_schedule=True
        ).order_by('eventpage__start_date')
    
    def get_events_by_type(self, event_type):
        """Returns events filtered by type"""
        return self.get_children().live().type(EventPage).filter(
            eventpage__event_type=event_type
        ).order_by('eventpage__start_date')
    
    def get_events_by_venue(self, place):
        """Returns events at a specific venue"""
        return self.get_children().live().type(EventPage).filter(
            eventpage__venue_place=place
        ).order_by('eventpage__start_date')
    
    def get_events_by_month(self, year, month):
        """Returns events for a specific month"""
        return self.get_children().live().type(EventPage).filter(
            eventpage__start_date__year=year,
            eventpage__start_date__month=month
        ).order_by('eventpage__start_date')