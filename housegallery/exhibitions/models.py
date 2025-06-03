from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django import forms

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel

from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.fields import StreamField, RichTextField
from wagtail.images.models import Image
from wagtail.images import get_image_model_string
from wagtail.models import Orderable
from wagtail.search import index
from wagtail.blocks import StructBlock, CharBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.models import register_snippet


from housegallery.core.mixins import Page, ListingFields
from housegallery.exhibitions.blocks import ExhibitionStreamBlock
from housegallery.core.blocks import BlankStreamBlock, TaggedSetBlock


class SelectImageBlock(StructBlock):
    """Block for selecting a single image"""
    image = ImageChooserBlock(required=True)
    caption = CharBlock(
        required=False,
        max_length=255,
        help_text="Optional caption for this image"
    )

    class Meta:
        template = 'components/exhibitions/select_image_block.html'
        icon = 'image'
        label = 'Select Image'




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
        FieldPanel('artist'),
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
        FieldPanel('artwork'),
    ]


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
    exhibition_images = StreamField([
        ('select_image', SelectImageBlock()),
        ('tagged_set', TaggedSetBlock()),
    ], blank=True, help_text="Images from the exhibition - use 'Select Image' for individual images or 'Tagged Set' for groups of images by tag")
    
    opening_images = StreamField([
        ('select_image', SelectImageBlock()),
        ('tagged_set', TaggedSetBlock()),
    ], blank=True, help_text="Images from the opening event - use 'Select Image' for individual images or 'Tagged Set' for groups of images by tag")

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
	    InlinePanel('exhibition_artists', label="Artists"),
	    InlinePanel('exhibition_artworks', label="Artworks"),
        FieldPanel('body'),
        MultiFieldPanel([
            FieldPanel('exhibition_images'),
            FieldPanel('opening_images'),
        ], heading="Image Galleries"),
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
    
    def get_all_gallery_images(self):
        """Get all images from both exhibition_images and opening_images StreamFields"""
        images = []
        
        # Process exhibition_images
        for block in self.exhibition_images:
            if block.block_type == 'select_image':
                if block.value.get('image'):
                    images.append({
                        'image': block.value['image'],
                        'caption': block.value.get('caption', ''),
                        'type': 'exhibition'
                    })
            elif block.block_type == 'tagged_set':
                tag = block.value.get('tag', '')
                if tag:
                    # Get images by tag
                    tagged_images = self._get_images_by_tag(tag)
                    for img in tagged_images:
                        images.append({
                            'image': img,
                            'caption': block.value.get('title', ''),
                            'type': 'exhibition'
                        })
        
        # Process opening_images
        for block in self.opening_images:
            if block.block_type == 'select_image':
                if block.value.get('image'):
                    images.append({
                        'image': block.value['image'],
                        'caption': block.value.get('caption', ''),
                        'type': 'opening'
                    })
            elif block.block_type == 'tagged_set':
                tag = block.value.get('tag', '')
                if tag:
                    # Get images by tag
                    tagged_images = self._get_images_by_tag(tag)
                    for img in tagged_images:
                        images.append({
                            'image': img,
                            'caption': block.value.get('title', ''),
                            'type': 'opening'
                        })
        
        return images
    
    def _get_images_by_tag(self, tag):
        """Helper method to get images by tag"""
        try:
            from housegallery.images.models import CustomImage
            return CustomImage.objects.filter(tags__name__iexact=tag).distinct()
        except:
            # Fallback to default image model if custom doesn't exist
            from wagtail.images import get_image_model
            ImageModel = get_image_model()
            return ImageModel.objects.filter(tags__name__iexact=tag).distinct()
        
    def get_current_date(self):
        """Return the current date for date comparisons."""
        from django.utils import timezone
        return timezone.now().date()

    def get_formatted_date_short(self):
        """Return a concise formatted date range (MM.DD format)."""
        if not self.start_date:
            return ""

        start_str = self.start_date.strftime("%m.%d")

        if self.end_date:
            end_str = self.end_date.strftime("%m.%d")
            return f"{start_str} - {end_str}"

        return start_str


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