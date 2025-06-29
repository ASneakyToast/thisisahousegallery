from wagtail.admin.panels import FieldPanel
from wagtail.snippets.widgets import AdminSnippetChooser


class ArtworkChooserWidget(AdminSnippetChooser):
    """
    Custom artwork chooser widget that uses the artwork chooser viewset
    with advanced filtering capabilities.
    """
    
    # Override the chooser URL name to use our custom chooser
    chooser_url_name = 'artwork_chooser:choose'
    
    def __init__(self, model=None, **kwargs):
        # Set default model if not provided
        if model is None:
            from housegallery.artworks.models import Artwork
            model = Artwork
        super().__init__(model=model, **kwargs)
    
    # Media will be inherited automatically from parent widget


class ArtworkChooserPanel(FieldPanel):
    """
    Custom field panel that uses the ArtworkChooserWidget
    for enhanced artwork selection with filtering.
    """
    
    def get_form_options(self):
        """Override to inject our custom widget."""
        opts = super().get_form_options()
        from housegallery.artworks.models import Artwork
        opts['widget'] = ArtworkChooserWidget(model=Artwork)
        return opts
    
    class Meta:
        # Inherit all parent meta options
        pass