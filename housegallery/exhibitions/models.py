from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.fields import StreamField, RichTextField
from wagtail.images.models import Image
from wagtail.images import get_image_model_string
from wagtail.models import Orderable
from wagtail.search import index


from housegallery.core.mixins import Page, ListingFields
#from housegallery.home.blocks import ExhibitionsStreamBlock
from housegallery.core.blocks import BlankStreamBlock


class ExhibitionsIndexPage(Page, ListingFields):
    """A page listing all exhibitions."""
    
    # body = StreamField(ExhibitionsStreamBlock())
    body = StreamField(BlankStreamBlock())
    
    template = 'pages/exhibitions/exhibitions_listing.html'
    
    parent_page_types = [
        'home.HomePage',
        'core.BlankPage'
    ]
    subpage_types = [
        'exhibitions.ExhibitionPage',
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
        """Add exhibitions to the context."""
        context = super().get_context(request)
        exhibitions = self.get_exhibitions()
        
        # Pagination
        page = request.GET.get('page')
        paginator = Paginator(exhibitions, 10)  # Show 10 exhibitions per page
        
        try:
            exhibitions = paginator.page(page)
        except PageNotAnInteger:
            exhibitions = paginator.page(1)
        except EmptyPage:
            exhibitions = paginator.page(paginator.num_pages)
            
        context['exhibitions'] = exhibitions
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
        return [ea.artist for ea in self.exhibition_artworks.all()]
