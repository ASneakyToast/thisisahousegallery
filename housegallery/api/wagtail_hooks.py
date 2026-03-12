from django.urls import reverse

from wagtail import hooks
from wagtail.admin.menu import Menu, MenuItem, SubmenuMenuItem

from .admin_viewsets import APIKeySnippetViewSet, ReadOnlyTokenSnippetViewSet


@hooks.register("register_admin_viewset")
def register_api_key_snippet_viewset():
    return APIKeySnippetViewSet()


@hooks.register("register_admin_viewset")
def register_readonly_token_snippet_viewset():
    return ReadOnlyTokenSnippetViewSet()


@hooks.register("construct_main_menu")
def add_api_menu(request, menu_items):
    """Add 'API' submenu to the Wagtail admin sidebar."""

    api_keys_item = MenuItem(
        "API Keys",
        reverse("wagtailsnippets_api_apikey:list"),
        icon_name="key",
        order=100,
    )

    readonly_tokens_item = MenuItem(
        "Read-Only Tokens",
        reverse("wagtailsnippets_api_readonlytoken:list"),
        icon_name="lock",
        order=200,
    )

    api_submenu = Menu(items=[api_keys_item, readonly_tokens_item])

    api_menu = SubmenuMenuItem(
        "API",
        api_submenu,
        icon_name="code",
        order=750,
    )

    menu_items.append(api_menu)
