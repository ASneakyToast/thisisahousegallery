from django.urls import reverse

from wagtail import hooks
from wagtail.admin.menu import Menu, MenuItem, SubmenuMenuItem

from .viewsets import gallery_kiosk_page_listing_viewset, simple_kiosk_page_listing_viewset


@hooks.register("register_admin_viewset")
def register_gallery_kiosk_page_listing_viewset():
    return gallery_kiosk_page_listing_viewset


@hooks.register("register_admin_viewset")
def register_simple_kiosk_page_listing_viewset():
    return simple_kiosk_page_listing_viewset


@hooks.register('construct_main_menu')
def add_kiosk_menu(request, menu_items):
    """Add Kiosk submenu with links to both kiosk type listings."""
    kiosk_submenu = Menu(items=[
        MenuItem('Gallery Kiosks', reverse('gallery_kiosk_pages:index'),
                 icon_name='desktop', order=100),
        MenuItem('Simple Kiosks', reverse('simple_kiosk_pages:index'),
                 icon_name='desktop', order=200),
    ])
    menu_items.append(SubmenuMenuItem(
        'Kiosk', kiosk_submenu, icon_name='desktop', order=800,
    ))
