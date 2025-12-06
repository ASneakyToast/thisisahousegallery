from django.urls import reverse
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.widgets import AdminSnippetChooser


class PlaceChooserWidget(AdminSnippetChooser):
    """
    Custom place chooser widget that uses the place chooser viewset
    with advanced filtering capabilities.
    """

    def __init__(self, model=None, **kwargs):
        if model is None:
            from housegallery.places.models import Place
            model = Place
        super().__init__(model=model, **kwargs)

    def get_chooser_modal_url(self):
        """Override to use our custom place chooser viewset with filtering."""
        return reverse('place_chooser:choose')


class PlaceChooserPanel(FieldPanel):
    """
    Custom field panel that uses the PlaceChooserWidget
    for enhanced place selection with filtering.
    """

    def get_form_options(self):
        """Override to inject our custom widget."""
        opts = super().get_form_options()
        from housegallery.places.models import Place
        # Must use "widgets" (plural) dict with field_name as key
        if "widgets" not in opts:
            opts["widgets"] = {}
        opts["widgets"][self.field_name] = PlaceChooserWidget(model=Place)
        return opts