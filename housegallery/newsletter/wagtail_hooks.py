from django.urls import reverse

from wagtail import hooks
from wagtail.admin.menu import Menu, MenuItem, SubmenuMenuItem
from wagtail.admin.widgets.button import Button

from .models import Newsletter
from .viewsets import (
    CampaignMediumSnippetViewSet,
    CampaignSourceSnippetViewSet,
    NewsletterSnippetViewSet,
    SubscriberSnippetViewSet,
    newsletter_signup_page_listing_viewset,
)


@hooks.register("register_admin_viewset")
def register_subscriber_snippet_viewset():
    return SubscriberSnippetViewSet()


@hooks.register("register_admin_viewset")
def register_newsletter_snippet_viewset():
    return NewsletterSnippetViewSet()


@hooks.register("register_admin_viewset")
def register_campaign_source_snippet_viewset():
    return CampaignSourceSnippetViewSet()


@hooks.register("register_admin_viewset")
def register_campaign_medium_snippet_viewset():
    return CampaignMediumSnippetViewSet()


@hooks.register("register_admin_viewset")
def register_newsletter_signup_page_listing_viewset():
    return newsletter_signup_page_listing_viewset


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

    signup_pages_item = MenuItem(
        'Signup Pages',
        reverse('newsletter_signup_pages:index'),
        icon_name='form',
        order=300,
    )

    unsubscribe_page_item = MenuItem(
        'Unsubscribe Page',
        reverse('newsletter:unsubscribe_request_page'),
        icon_name='link-external',
        attrs={"target": "_blank"},
        order=400,
    )

    email_settings_item = MenuItem(
        'Email Settings',
        reverse('wagtailsettings:edit', args=['newsletter', 'newsletteremailsettings']),
        icon_name='cog',
        order=500,
    )

    newsletter_submenu = Menu(items=[
        subscribers_item,
        newsletters_item,
        signup_pages_item,
        unsubscribe_page_item,
        email_settings_item,
    ])

    newsletter_menu = SubmenuMenuItem(
        'Newsletter',
        newsletter_submenu,
        icon_name='mail',
        order=700
    )

    menu_items.append(newsletter_menu)


@hooks.register("register_snippet_listing_buttons")
def newsletter_listing_buttons(instance, user, next_url):
    if not isinstance(instance, Newsletter):
        return []

    label = "Send\u2026"
    return [
        Button(
            label=label,
            url=reverse(
                "wagtailsnippets_newsletter_newsletter:send",
                args=[instance.pk],
            ),
            icon_name="mail",
            priority=10,
        ),
    ]
