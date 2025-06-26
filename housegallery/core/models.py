from django.db import models

from modelcluster.models import ClusterableModel

from wagtail import blocks
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, PageChooserPanel
from wagtail.admin.menu import MenuItem
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.blocks.struct_block import StructBlockAdapter
from wagtail.fields import StreamField
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from housegallery.core.blocks import BlankStreamBlock
from housegallery.core.mixins import Page, ListingFields
from housegallery.core.utils import LinkBlock, LinkBlockStructValue


# NAVIGATION #

@register_snippet
class NavigationMenu(ClusterableModel):
    title = models.CharField(
        max_length=100,
        null=False,
        blank=False,
        default='menu',
        help_text="Title for this list o' links."
    )
    links = StreamField(blocks.StreamBlock(
        [
            ('normal_link', blocks.StructBlock([
                ('link', LinkBlock()),
                ('is_cta', blocks.BooleanBlock(
                    required=False,
                    default=False,
                    help_text="CTA links show up in special places (like the header.)"
                )),
                ('open_in_new_tab', blocks.BooleanBlock(
                    required=False,
                    default=False,
                    help_text="Want this link to open in a new tab?"
                )),
            ], icon='link')),
            ('divider', blocks.StructBlock([
                ('label', blocks.CharBlock(
                    required=False,
                    max_length=50,
                    help_text="Optional text label for this menu section (leave blank for just a line)"
                )),
            ], icon='grip'))
        ], required=False,
    ), blank=True)
    
    panels = [
        FieldPanel('title'),
        FieldPanel('links'),
    ]
    
    def __str__(self):
        return self.title


@register_setting
class NavigationSettings(BaseSiteSetting):
    main_menu = models.ForeignKey(
        'core.NavigationMenu',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Select the menu to be displayed in the site header'
    )

    panels = [
        FieldPanel('main_menu'),
    ]


# STANDARD PAGES #

class BlankPage(Page, ListingFields):
    """Blank base page for cms editors and related content."""

    body = StreamField(BlankStreamBlock())

    template = 'pages/generics/blank.html'

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

