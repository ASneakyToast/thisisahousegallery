from wagtail.admin.panels import FieldPanel
from wagtail.images.widgets import AdminImageChooser


class ExhibitionImageChooserWidget(AdminImageChooser):
    """
    Custom image chooser widget that uses the exhibition image chooser viewset
    with advanced filtering capabilities.
    """
    
    # Override the chooser URL name to use our custom chooser
    chooser_url_name = 'exhibition_image_chooser:choose'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    # Media will be inherited automatically from parent widget


class ExhibitionImageChooserPanel(FieldPanel):
    """
    Custom field panel that uses the ExhibitionImageChooserWidget
    for enhanced image selection with filtering.
    """
    
    def get_form_options(self):
        """Override to inject our custom widget."""
        opts = super().get_form_options()
        opts['widget'] = ExhibitionImageChooserWidget()
        return opts
    
    class Meta:
        # Inherit all parent meta options
        pass