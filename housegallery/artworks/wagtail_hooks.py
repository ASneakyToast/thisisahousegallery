from wagtail import hooks
from .views import artwork_chooser_viewset
from .viewsets import ArtworkSnippetViewSet

@hooks.register('register_admin_viewset')
def register_artwork_chooser_viewset():
    return artwork_chooser_viewset

@hooks.register('register_admin_viewset') 
def register_artwork_snippet_viewset():
    return ArtworkSnippetViewSet()