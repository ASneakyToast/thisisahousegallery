from django.urls import reverse
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.widgets import AdminSnippetChooser


class ArtworkChooserWidget(AdminSnippetChooser):
    """
    Custom artwork chooser widget that uses the artwork chooser viewset
    with advanced filtering capabilities.
    """

    def __init__(self, model=None, **kwargs):
        if model is None:
            from housegallery.artworks.models import Artwork
            model = Artwork
        super().__init__(model=model, **kwargs)

    def get_chooser_modal_url(self):
        """Override to use our custom artwork chooser viewset with filtering."""
        return reverse('artwork_chooser:choose')


class ArtworkChooserPanel(FieldPanel):
    """
    Custom field panel that uses the ArtworkChooserWidget
    for enhanced artwork selection with filtering.
    """

    def get_form_options(self):
        """Override to inject our custom widget."""
        opts = super().get_form_options()
        from housegallery.artworks.models import Artwork
        # Must use "widgets" (plural) dict with field_name as key
        if "widgets" not in opts:
            opts["widgets"] = {}
        opts["widgets"][self.field_name] = ArtworkChooserWidget(model=Artwork)
        return opts