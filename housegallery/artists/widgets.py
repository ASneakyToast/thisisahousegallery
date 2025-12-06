from django.urls import reverse
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.widgets import AdminSnippetChooser


class ArtistChooserWidget(AdminSnippetChooser):
    """
    Custom artist chooser widget that uses the artist chooser viewset
    with advanced filtering capabilities and thumbnail previews.
    """
    template_name = "artists/widgets/artist_chooser.html"

    def __init__(self, model=None, **kwargs):
        if model is None:
            from housegallery.artists.models import Artist
            model = Artist
        super().__init__(model=model, **kwargs)

    def get_chooser_modal_url(self):
        """Override to use our custom artist chooser viewset with filtering."""
        return reverse('artist_chooser:choose')

    def get_context(self, name, value_data, attrs):
        """Add preview data to context if artist has profile image."""
        context = super().get_context(name, value_data, attrs)
        # value_data is a dict with 'id' key containing the actual PK
        pk = value_data.get("id") if isinstance(value_data, dict) else value_data
        if pk:
            from housegallery.artists.models import Artist
            try:
                artist = Artist.objects.get(pk=pk)
                if artist.profile_image:
                    preview = artist.profile_image.get_rendition("max-165x165")
                    context["preview"] = {
                        "url": preview.url,
                        "width": preview.width,
                        "height": preview.height,
                    }
            except (Artist.DoesNotExist, Exception):
                pass
        return context


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