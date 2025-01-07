from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, PageChooserPanel
from wagtail.admin.widgets.slug import SlugInput
from wagtail.fields import RichTextField
from wagtail.images import get_image_model_string
from wagtail.models import Page as WagtailPage
from wagtail.search import index

from housegallery.core.rich_text import MINIMAL_RICHTEXT


# Generic listing fields abstract class to add listing image/text to any new content type easily.
class ListingFields(models.Model):
    listing_image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Choose the image you wish to be displayed when this page appears in listings",
    )
    listing_title = models.CharField(max_length=255, blank=True, help_text="Override the page title used when this page appears in listings")
    listing_summary = RichTextField(
        max_length=255,
        blank=True,
        null=True,
        features=MINIMAL_RICHTEXT,
        # validators=[RichTextLengthValidator(max_length=255)], # no need no more
        help_text="The text summary used when this page appears in listings. \
                   It's also used as the description for search engines if the \
                   'Search description' field above is not defined. Max Length: 255"
    )
    exclude_from_search = models.BooleanField(
        default=False,
        help_text="If checked, this page will not appear in site search results"
    )

    class Meta:
        abstract = True

    search_fields = [
        index.SearchField('listing_title'),
        index.SearchField('listing_summary'),
    ]

    promote_panels = [
        MultiFieldPanel([
            FieldPanel('listing_image'),
            FieldPanel('listing_title'),
            FieldPanel('listing_summary'),
            FieldPanel('exclude_from_search'),
        ], 'Listing information'),
    ]


class Page(WagtailPage):
    """Abstract base page with common fields for all pages."""

    promote_panels = [
        MultiFieldPanel([
            FieldPanel('slug', widget=SlugInput),
            FieldPanel('seo_title'),
            FieldPanel('search_description'),
        ], 'Common page configuration')
    ]

    class Meta:
        abstract = True
