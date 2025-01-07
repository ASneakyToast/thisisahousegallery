from wagtail.admin.panels import FieldPanel, MultiFieldPanel, PageChooserPanel
from wagtail.fields import StreamField
from wagtail.search import index

from housegallery.core.mixins import Page, ListingFields
from housegallery.home.blocks import HomeStreamBlock


class HomePage(Page, ListingFields):

    body = StreamField(HomeStreamBlock())

    template = 'pages/home.html'

    # Only allow creating HomePages at the root level
    parent_page_types = ['wagtailcore.Page']

    subpage_types = [
        'exhibitions.ExhibitionsIndexPage',
        'exhibitions.SchedulePage',
        'core.BlankPage'
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
