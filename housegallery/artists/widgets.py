from wagtail.admin.panels import FieldPanel
from wagtail.snippets.widgets import AdminSnippetChooser


class ArtistChooserWidget(AdminSnippetChooser):
    """
    Custom artist chooser widget that uses the artist chooser viewset
    with advanced filtering capabilities.
    """
    
    # Override the chooser URL name to use our custom chooser
    chooser_url_name = 'artist_chooser:choose'
    
    def __init__(self, model=None, **kwargs):
        # Set default model if not provided
        if model is None:
            from housegallery.artists.models import Artist
            model = Artist
        super().__init__(model=model, **kwargs)
    
    # Media will be inherited automatically from parent widget


class ArtistChooserPanel(FieldPanel):
    """
    Custom field panel that uses the ArtistChooserWidget
    for enhanced artist selection with filtering.
    """
    
    def get_form_options(self):
        """Override to inject our custom widget."""
        opts = super().get_form_options()
        from housegallery.artists.models import Artist
        opts['widget'] = ArtistChooserWidget(model=Artist)
        return opts
    
    class Meta:
        # Inherit all parent meta options
        pass