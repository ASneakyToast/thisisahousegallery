from wagtail.snippets.views.snippets import SnippetViewSet

from .models import Newsletter, Subscriber


class SubscriberSnippetViewSet(SnippetViewSet):
    model = Subscriber
    icon = "mail"
    menu_label = "Subscribers"
    menu_name = "subscribers"
    menu_order = 300
    add_to_settings_menu = False
    add_to_admin_menu = False

    list_display = ["email", "confirmed", "created_at", "confirmed_at", "unsubscribed_at"]
    list_filter = ["confirmed"]
    list_per_page = 50
    ordering = ["-created_at"]
    search_fields = ["email"]
    list_export = ["email", "confirmed", "created_at", "confirmed_at", "unsubscribed_at"]


class NewsletterSnippetViewSet(SnippetViewSet):
    model = Newsletter
    icon = "doc-full-inverse"
    menu_label = "Newsletters"
    menu_name = "newsletters"
    menu_order = 310
    add_to_settings_menu = False
    add_to_admin_menu = False

    list_display = ["title", "slug", "status", "sent_count", "sent_at", "created_at"]
    list_filter = ["status"]
    list_per_page = 50
    ordering = ["-created_at"]
    search_fields = ["title", "slug"]
