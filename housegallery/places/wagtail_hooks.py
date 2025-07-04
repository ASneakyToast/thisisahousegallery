from wagtail import hooks
from .views import place_chooser_viewset


@hooks.register('register_admin_viewset')
def register_place_chooser_viewset():
    return place_chooser_viewset