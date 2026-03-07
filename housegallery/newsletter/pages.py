from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.search import index

from housegallery.core.blocks import BlankStreamBlock
from housegallery.core.mixins import ListingFields, Page


class NewsletterSignupPage(Page, ListingFields):
    """CMS-editable landing page with an embedded newsletter signup form."""

    intro = RichTextField(blank=True, help_text="Introductory text above the signup form.")
    body = StreamField(BlankStreamBlock(), blank=True, help_text="Additional content below the signup form.")

    template = "pages/newsletter/signup_page.html"

    parent_page_types = ["home.HomePage", "core.BlankPage"]
    subpage_types = []

    search_fields = Page.search_fields + ListingFields.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body"),
    ]

    promote_panels = Page.promote_panels + ListingFields.promote_panels

    def get_context(self, request):
        context = super().get_context(request)
        ref = request.GET.get("ref", "").strip()
        campaign = None
        if ref:
            from housegallery.newsletter.models import Campaign

            campaign = Campaign.objects.filter(slug=ref, is_active=True).first()
        context["ref"] = ref if campaign else ""
        context["campaign"] = campaign
        return context
