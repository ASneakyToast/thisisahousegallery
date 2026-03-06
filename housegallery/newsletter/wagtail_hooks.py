from django.urls import reverse

from wagtail import hooks
from wagtail.admin.menu import Menu, MenuItem, SubmenuMenuItem

from .viewsets import NewsletterSnippetViewSet, SubscriberSnippetViewSet


@hooks.register("register_admin_viewset")
def register_subscriber_snippet_viewset():
    return SubscriberSnippetViewSet()


@hooks.register("register_admin_viewset")
def register_newsletter_snippet_viewset():
    return NewsletterSnippetViewSet()


@hooks.register('construct_main_menu')
def add_newsletter_menu(request, menu_items):
    """Add custom Newsletter menu with Subscribers and Newsletters submenus."""

    subscribers_item = MenuItem(
        'Subscribers',
        reverse('wagtailsnippets_newsletter_subscriber:list'),
        icon_name='group',
        order=100
    )

    newsletters_item = MenuItem(
        'Newsletters',
        reverse('wagtailsnippets_newsletter_newsletter:list'),
        icon_name='mail',
        order=200
    )

    newsletter_submenu = Menu(items=[subscribers_item, newsletters_item])

    newsletter_menu = SubmenuMenuItem(
        'Newsletter',
        newsletter_submenu,
        icon_name='mail',
        order=700
    )

    menu_items.append(newsletter_menu)
