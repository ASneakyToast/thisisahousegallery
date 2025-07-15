from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, PageChooserPanel
from wagtail.fields import StreamField
from wagtail.search import index

from housegallery.core.mixins import Page, ListingFields
from housegallery.home.blocks import HomeStreamBlock, KioskStreamBlock


class HomePage(Page, ListingFields):

    body = StreamField(HomeStreamBlock())

    template = 'pages/home.html'

    # Only allow creating HomePages at the root level
    parent_page_types = ['wagtailcore.Page']

    subpage_types = [
        'exhibitions.ExhibitionsIndexPage',
        'exhibitions.SchedulePage',
        'places.PlacesIndexPage',
        'core.BlankPage',
        'home.KioskPage'
    ] 

    search_fields = Page.search_fields + ListingFields.search_fields + [
        index.SearchField('body'),
    ]
    # search_fields = Page.search_fields + ListingFields.search_fields # without body

    content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]

    promote_panels = (
        Page.promote_panels
        + ListingFields.promote_panels
    )


class KioskPage(Page):
    """
    A fullscreen kiosk page for displaying an animated gallery at /display.
    Singleton page type to prevent multiple instances.
    """
    
    body = StreamField(KioskStreamBlock(), blank=True)
    
    # Gallery title displayed prominently on the kiosk
    gallery_title = models.CharField(
        max_length=255,
        default="This is a House Gallery",
        help_text="Main title displayed on the kiosk screen"
    )
    
    # Mailing list settings
    enable_mailing_list = models.BooleanField(
        default=True,
        help_text="Show mailing list subscription form on kiosk"
    )
    
    mailing_list_prompt = models.CharField(
        max_length=255,
        default="Stay connected with our gallery",
        help_text="Text to encourage mailing list subscription"
    )
    
    # Animation settings
    auto_advance_seconds = models.PositiveIntegerField(
        default=8,
        help_text="Seconds between automatic image transitions (0 to disable)"
    )
    
    show_image_count = models.PositiveIntegerField(
        default=12,
        help_text="Maximum number of images to display simultaneously"
    )

    template = 'pages/kiosk_page.html'

    # Singleton - only allow one kiosk page
    parent_page_types = ['home.HomePage']
    subpage_types = []
    max_count = 1

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.SearchField('gallery_title'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('gallery_title'),
        FieldPanel('body'),
        MultiFieldPanel([
            FieldPanel('enable_mailing_list'),
            FieldPanel('mailing_list_prompt'),
        ], heading="Mailing List Settings"),
        MultiFieldPanel([
            FieldPanel('auto_advance_seconds'),
            FieldPanel('show_image_count'),
        ], heading="Animation Settings"),
    ]
    
    class Meta:
        verbose_name = "Kiosk Display Page"
        verbose_name_plural = "Kiosk Display Pages"
