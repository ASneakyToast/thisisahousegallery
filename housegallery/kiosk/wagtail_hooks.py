from wagtail import hooks

from .viewsets import kiosk_page_listing_viewset


@hooks.register("register_admin_viewset")
def register_kiosk_page_listing_viewset():
    return kiosk_page_listing_viewset
