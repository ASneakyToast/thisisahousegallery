from wagtail.admin.ui.tables import LiveStatusTagColumn
from wagtail.admin.viewsets.pages import PageListingViewSet

from .models import KioskPage


class KioskPageListingViewSet(PageListingViewSet):
    model = KioskPage
    icon = "desktop"
    menu_label = "Kiosks"
    name = "kiosk_pages"
    add_to_admin_menu = True
    menu_order = 800
    columns = PageListingViewSet.columns + [
        LiveStatusTagColumn(),
    ]


kiosk_page_listing_viewset = KioskPageListingViewSet("kiosk_pages")
