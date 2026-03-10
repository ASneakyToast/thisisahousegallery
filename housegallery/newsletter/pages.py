from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.search import index

from housegallery.core.blocks import BlankStreamBlock
from housegallery.core.mixins import ListingFields, Page


class NewsletterSignupPage(Page, ListingFields):
    """CMS-editable landing page with an embedded newsletter signup form.

    The generic signup page lives at /subscribe/. Campaign-specific pages
    are children (e.g. /subscribe/spring-exhibition/) and carry tracking
    fields (source, medium, campaign_name).
    """

    intro = RichTextField(blank=True, help_text="Introductory text above the signup form.")
    body = StreamField(BlankStreamBlock(), blank=True, help_text="Additional content below the signup form.")

    source = models.ForeignKey(
        "newsletter.CampaignSource", null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="Traffic source for this campaign page.",
    )
    medium = models.ForeignKey(
        "newsletter.CampaignMedium", null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="Marketing medium for this campaign page.",
    )
    campaign_name = models.CharField(
        max_length=255, blank=True,
        help_text="UTM campaign name (e.g., 'spring-exhibition-2026').",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive pages won't accept new signups.",
    )

    template = "pages/newsletter/signup_page.html"

    parent_page_types = ["home.HomePage", "core.BlankPage", "newsletter.NewsletterSignupPage"]
    subpage_types = ["newsletter.NewsletterSignupPage"]

    search_fields = Page.search_fields + ListingFields.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body"),
    ]

    promote_panels = Page.promote_panels + ListingFields.promote_panels

    settings_panels = Page.settings_panels + [
        MultiFieldPanel([
            FieldPanel("source"),
            FieldPanel("medium"),
            FieldPanel("campaign_name"),
            FieldPanel("is_active"),
        ], heading="Campaign Tracking"),
    ]

    @property
    def signup_count(self):
        return self.subscribers.count()

    @property
    def confirmed_count(self):
        return self.subscribers.filter(confirmed=True, unsubscribed_at__isnull=True).count()
