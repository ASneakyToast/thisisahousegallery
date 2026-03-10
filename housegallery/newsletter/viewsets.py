from functools import cached_property

from django.urls import path, reverse
from wagtail.admin.ui.tables import BooleanColumn, Column, LiveStatusTagColumn
from wagtail.admin.viewsets.pages import PageListingViewSet
from wagtail.admin.widgets.button import Button
from wagtail.snippets.views.snippets import EditView, SnippetViewSet

from .admin_views import SendNewsletterView
from .models import CampaignMedium, CampaignSource, Newsletter, Subscriber
from .pages import NewsletterSignupPage


class NewsletterEditView(EditView):
    @cached_property
    def header_more_buttons(self):
        buttons = super().header_more_buttons
        newsletter = self.object

        label = (
            "Resend Newsletter"
            if newsletter.status == Newsletter.Status.SENT
            else "Send Newsletter"
        )
        send_button = Button(
            label,
            url=reverse(
                "wagtailsnippets_newsletter_newsletter:send",
                args=[newsletter.pk],
            ),
            icon_name="mail",
            priority=1,
        )
        preview_button = Button(
            "Preview",
            url=reverse("newsletter:preview", args=[newsletter.slug]),
            icon_name="doc-full",
            attrs={"target": "_blank"},
            priority=2,
        )
        return [send_button, preview_button] + buttons


class SubscriberSnippetViewSet(SnippetViewSet):
    model = Subscriber
    icon = "mail"
    menu_label = "Subscribers"
    menu_name = "subscribers"
    menu_order = 300
    add_to_settings_menu = False
    add_to_admin_menu = False

    list_display = [
        "email", "confirmed", "signup_page", "bounce_count", "last_bounced_at",
        "created_at", "confirmed_at", "unsubscribed_at",
    ]
    list_filter = ["confirmed", "bounce_count"]
    list_per_page = 50
    ordering = ["-created_at"]
    search_fields = ["email"]
    list_export = [
        "email", "confirmed", "signup_page", "bounce_count", "last_bounced_at",
        "created_at", "confirmed_at", "unsubscribed_at",
    ]


class CampaignSourceSnippetViewSet(SnippetViewSet):
    model = CampaignSource
    icon = "tag"
    menu_label = "Campaign Sources"
    menu_name = "campaign_sources"
    add_to_settings_menu = False
    add_to_admin_menu = False

    list_display = ["name"]
    search_fields = ["name"]


class CampaignMediumSnippetViewSet(SnippetViewSet):
    model = CampaignMedium
    icon = "tag"
    menu_label = "Campaign Media"
    menu_name = "campaign_media"
    add_to_settings_menu = False
    add_to_admin_menu = False

    list_display = ["name"]
    search_fields = ["name"]


class NewsletterSignupPageListingViewSet(PageListingViewSet):
    model = NewsletterSignupPage
    icon = "form"
    menu_label = "Signup Pages"
    name = "newsletter_signup_pages"
    add_to_admin_menu = False
    columns = PageListingViewSet.columns + [
        Column("source", label="Source"),
        Column("medium", label="Medium"),
        Column("campaign_name", label="Campaign"),
        BooleanColumn("is_active", label="Active"),
        LiveStatusTagColumn(),
    ]


newsletter_signup_page_listing_viewset = NewsletterSignupPageListingViewSet(
    "newsletter_signup_pages"
)


class NewsletterSnippetViewSet(SnippetViewSet):
    model = Newsletter
    icon = "doc-full-inverse"
    menu_label = "Newsletters"
    menu_name = "newsletters"
    menu_order = 310
    add_to_settings_menu = False
    add_to_admin_menu = False

    edit_view_class = NewsletterEditView

    list_display = ["title", "slug", "status", "sent_count", "sent_at", "created_at"]
    list_filter = ["status"]
    list_per_page = 50
    ordering = ["-created_at"]
    search_fields = ["title", "slug"]

    def get_urlpatterns(self):
        urlpatterns = super().get_urlpatterns()
        urlpatterns += [
            path(
                "send/<str:pk>/",
                SendNewsletterView.as_view(),
                name="send",
            ),
        ]
        return urlpatterns
