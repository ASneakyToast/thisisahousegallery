from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from housegallery.artists.models import Artist
from housegallery.images.models import CustomImage


class BulkArtworkDefaultsForm(forms.Form):
    """Shared defaults applied to all artworks in a bulk add batch."""

    artists = forms.ModelMultipleChoiceField(
        queryset=Artist.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=_("Artist(s)"),
    )
    materials = forms.CharField(
        required=False,
        label=_("Materials"),
        help_text=_("Comma-separated tag names, e.g. 'oil, canvas, mixed media'"),
    )
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label=_("Date"),
    )
    price = forms.CharField(
        required=False,
        max_length=50,
        label=_("Price"),
        help_text=_("e.g. $500, NFS, Sold, Price on request"),
    )


class BulkArtworkRowForm(forms.Form):
    """Per-artwork row in the bulk add form."""

    title = forms.CharField(required=False, max_length=255)
    image = forms.IntegerField(required=False, widget=forms.HiddenInput)
    description = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.Textarea(attrs={"rows": 2}),
    )
    width_inches = forms.DecimalField(
        required=False, max_digits=7, decimal_places=3, min_value=0,
    )
    height_inches = forms.DecimalField(
        required=False, max_digits=7, decimal_places=3, min_value=0,
    )
    depth_inches = forms.DecimalField(
        required=False, max_digits=7, decimal_places=3, min_value=0,
    )
    size = forms.CharField(required=False, max_length=255)
    price = forms.CharField(required=False, max_length=50)
    materials = forms.CharField(required=False)

    def clean_image(self):
        image_id = self.cleaned_data.get("image")
        if image_id is not None:
            if not CustomImage.objects.filter(pk=image_id).exists():
                raise ValidationError(_("Image with this ID does not exist."))
        return image_id

    def is_empty(self):
        """Return True if all fields are blank/None."""
        if not hasattr(self, "cleaned_data"):
            return True
        return not any(
            self.cleaned_data.get(f)
            for f in [
                "title", "image", "description", "width_inches",
                "height_inches", "depth_inches", "size", "price", "materials",
            ]
        )


class BaseBulkArtworkFormSet(forms.BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        has_non_empty = False
        for form in self.forms:
            if not form.cleaned_data.get("DELETE", False) and not form.is_empty():
                has_non_empty = True
                break
        if not has_non_empty:
            raise ValidationError(
                _("At least one row must have data."), code="all_empty",
            )


BulkArtworkFormSet = forms.formset_factory(
    BulkArtworkRowForm,
    formset=BaseBulkArtworkFormSet,
    extra=5,
    max_num=50,
    min_num=0,
    validate_min=False,
    validate_max=True,
    can_delete=True,
)
