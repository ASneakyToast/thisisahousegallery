from wagtail import hooks
from .views import artist_chooser_viewset

@hooks.register('register_admin_viewset')
def register_artist_chooser_viewset():
    return artist_chooser_viewset