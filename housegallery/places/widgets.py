from wagtail.admin.panels import FieldPanel
from wagtail.snippets.widgets import AdminSnippetChooser


class PlaceChooserWidget(AdminSnippetChooser):
    """
    Custom place chooser widget that uses the place chooser viewset
    with advanced filtering capabilities.
    """
    
    # Override the chooser URL name to use our custom chooser
    chooser_url_name = 'place_chooser:choose'
    
    def __init__(self, model=None, **kwargs):
        # Set default model if not provided
        if model is None:
            from housegallery.places.models import Place
            model = Place
        super().__init__(model=model, **kwargs)
    
    # Media will be inherited automatically from parent widget


class PlaceChooserPanel(FieldPanel):
    """
    Custom field panel that uses the PlaceChooserWidget
    for enhanced place selection with filtering.
    """
    
    def get_form_options(self):
        """Override to inject our custom widget."""
        opts = super().get_form_options()
        from housegallery.places.models import Place
        opts['widget'] = PlaceChooserWidget(model=Place)
        return opts
    
    class Meta:
        # Inherit all parent meta options
        pass