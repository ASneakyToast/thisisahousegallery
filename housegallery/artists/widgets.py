from django.urls import reverse
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.widgets import AdminSnippetChooser


class ArtistChooserWidget(AdminSnippetChooser):
    """
    Custom artist chooser widget that uses the artist chooser viewset
    with advanced filtering capabilities.
    """

    def __init__(self, model=None, **kwargs):
        if model is None:
            from housegallery.artists.models import Artist
            model = Artist
        super().__init__(model=model, **kwargs)

    def get_chooser_modal_url(self):
        """Override to use our custom artist chooser viewset with filtering."""
        return reverse('artist_chooser:choose')


class ArtistChooserPanel(FieldPanel):
    """
    Custom field panel that uses the ArtistChooserWidget
    for enhanced artist selection with filtering.
    """

    def get_form_options(self):
        """Override to inject our custom widget."""
        opts = super().get_form_options()
        from housegallery.artists.models import Artist
        # Must use "widgets" (plural) dict with field_name as key
        if "widgets" not in opts:
            opts["widgets"] = {}
        opts["widgets"][self.field_name] = ArtistChooserWidget(model=Artist)
        return opts