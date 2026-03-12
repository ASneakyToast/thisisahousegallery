from wagtail.admin.ui.tables import Column
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import APIKey, ReadOnlyToken


class APIKeySnippetViewSet(SnippetViewSet):
    model = APIKey
    icon = "key"
    menu_label = "API Keys"
    menu_name = "api_keys"
    add_to_settings_menu = False
    add_to_admin_menu = False

    list_display = [
        "name",
        "artist",
        "is_active",
        "rate_limit",
        "created",
        "last_used",
        "usage_count",
    ]
    list_filter = ["is_active", "artist"]
    ordering = ["-created"]
    search_fields = ["name", "artist__name"]


class ReadOnlyTokenSnippetViewSet(SnippetViewSet):
    model = ReadOnlyToken
    icon = "lock"
    menu_label = "Read-Only Tokens"
    menu_name = "readonly_tokens"
    add_to_settings_menu = False
    add_to_admin_menu = False

    list_display = [
        "name",
        "is_active",
        Column("key", label="Token", accessor=lambda obj: obj.key[:12] + "…"),
        "created",
        "last_used",
        "usage_count",
    ]
    list_filter = ["is_active"]
    ordering = ["-created"]
    search_fields = ["name"]
