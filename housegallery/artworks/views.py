from functools import cached_property

from django import forms
from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models import Q, F
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail.admin.forms.choosers import BaseFilterForm, LocaleFilterMixin
from wagtail.admin.ui.tables import TitleColumn, Column
from wagtail.admin.views.generic.chooser import (BaseChooseView,
                                                 ChooseResultsViewMixin,
                                                 ChooseViewMixin,
                                                 CreationFormMixin)
from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.models import TranslatableMixin


class ArtworkSearchFilterMixin(forms.Form):
    """Search filter mixin for Artwork model with artwork-focused filters."""
    
    q = forms.CharField(
        label=_("Search term"),
        widget=forms.TextInput(attrs={"placeholder": _("Search artworks by title, description, or artist...")}),
        required=False,
    )
    
    artist = forms.ModelChoiceField(
        label=_("Artist"),
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label=_("All artists"),
        widget=forms.Select(attrs={"class": "form-select"})
    )
    
    materials = forms.MultipleChoiceField(
        label=_("Materials"),
        widget=forms.SelectMultiple(attrs={
            "class": "form-control",
            "size": "6",
            "style": "height: auto;"
        }),
        required=False,
        help_text=_("Select one or more materials to filter artworks.")
    )
    
    date_from = forms.DateField(
        label=_("Created from"),
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    
    date_to = forms.DateField(
        label=_("Created to"),
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    
    size_category = forms.ChoiceField(
        label=_("Size Category"),
        required=False,
        choices=[
            ('', _('All sizes')),
            ('small', _('Small works')),
            ('medium', _('Medium works')),
            ('large', _('Large works')),
        ],
        widget=forms.Select(attrs={"class": "form-select"})
    )
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Import here to avoid circular imports
        from housegallery.artists.models import Artist
        from taggit.models import Tag
        
        # Populate artist choices
        self.fields['artist'].queryset = Artist.objects.all().order_by('name')
        
        # Populate material choices from tags used by artworks
        # Get all tags used in artwork materials
        from housegallery.artworks.models import Artwork
        artwork_tags = Tag.objects.filter(
            taggit_taggeditem_items__content_type__model='artwork'
        ).distinct().order_by('name')
        material_choices = [(tag.name, tag.name) for tag in artwork_tags]
        self.fields['materials'].choices = material_choices

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        # Validate date range
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError(_('Created from date must be before created to date.'))
        
        return cleaned_data

    def filter(self, objects):
        # Text search across multiple fields
        search_query = self.cleaned_data.get("q")
        if search_query:
            objects = objects.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(artists__name__icontains=search_query)
            ).distinct()
            
        # Artist filtering
        artist_filter = self.cleaned_data.get("artist")
        if artist_filter:
            objects = objects.filter(artists=artist_filter)
            
        # Materials filtering with multi-select
        materials_filter = self.cleaned_data.get("materials")
        if materials_filter:
            objects = objects.filter(materials__name__in=materials_filter).distinct()
            
        # Date range filtering
        date_from = self.cleaned_data.get("date_from")
        if date_from:
            objects = objects.filter(date__gte=date_from)
            
        date_to = self.cleaned_data.get("date_to")
        if date_to:
            objects = objects.filter(date__lte=date_to)
            
        # Size category filtering (basic implementation)
        size_category = self.cleaned_data.get("size_category")
        if size_category:
            if size_category == 'small':
                # Artworks with size field containing keywords suggesting small size
                objects = objects.filter(
                    Q(size__icontains='small') |
                    Q(size__iregex=r'\b\d{1,2}["\s]') |  # Less than 100 inches/cm
                    Q(size__iregex=r'\b[1-9]\d{0,1}\s*(cm|in)')  # 1-99 cm/in
                )
            elif size_category == 'medium':
                # Medium sized works
                objects = objects.filter(
                    Q(size__icontains='medium') |
                    Q(size__iregex=r'\b1\d{2}["\s]') |  # 100-199 range
                    Q(size__iregex=r'\b[1-9]\d{2}\s*(cm|in)')  # 100-999 cm/in
                )
            elif size_category == 'large':
                # Large works
                objects = objects.filter(
                    Q(size__icontains='large') |
                    Q(size__iregex=r'\b[2-9]\d{2}["\s]') |  # 200+ range
                    Q(size__iregex=r'\b\d{4,}\s*(cm|in)')  # 1000+ cm/in
                )
                
            
        return objects


class BaseArtworkChooseView(BaseChooseView):
    """Base chooser view for Artwork model with artwork-focused columns."""
    ordering = ["-date", "title"]  # Sort by date desc, then title
    
    def get_queryset(self):
        """Optimize queryset to avoid N+1 queries"""
        return super().get_queryset().prefetch_related('artists', 'materials')
    
    @property
    def columns(self):
        return [
            TitleColumn(
                name="title",
                label=_("Title"),
                url_name=self.chosen_url_name,
                link_attrs={"data-chooser-modal-choice": True},
            ),
            Column(
                name="artists",
                label=_("Artist(s)"),
                accessor=lambda obj: obj.artist_names if obj.artist_names else '-',
            ),
            Column(
                name="materials",
                label=_("Materials"),
                accessor=lambda obj: ', '.join([tag.name for tag in obj.materials.all()]) or '-',
            ),
            Column(
                name="size",
                label=_("Size"),
                accessor=lambda obj: obj.size or '-',
            ),
            Column(
                name="date",
                label=_("Date"),
                accessor=lambda obj: obj.date.strftime('%Y-%m-%d') if obj.date else '-',
            ),
            Column(
                name="description",
                label=_("Description"),
                accessor=lambda obj: (obj.description[:50] + '...') if len(obj.description or '') > 50 else (obj.description or '-'),
            ),
        ]

    def get_filter_form_class(self):
        bases = [ArtworkSearchFilterMixin, BaseFilterForm]

        i18n_enabled = getattr(settings, "WAGTAIL_I18N_ENABLED", False)
        if i18n_enabled and issubclass(self.model_class, TranslatableMixin):
            bases.insert(0, LocaleFilterMixin)

        return type(
            "FilterForm",
            tuple(bases),
            {},
        )


class ArtworkChooseView(ChooseViewMixin, CreationFormMixin, BaseArtworkChooseView):
    pass


class ArtworkChooseResultsView(ChooseResultsViewMixin, CreationFormMixin, BaseArtworkChooseView):
    pass


class ArtworkChooserViewSet(ChooserViewSet):
    model = 'artworks.Artwork'

    choose_view_class = ArtworkChooseView
    choose_results_view_class = ArtworkChooseResultsView

    icon = "snippet"
    choose_one_text = _("Choose an artwork")
    choose_another_text = _("Choose another artwork")
    paginate_by = getattr(settings, 'DEFAULT_PER_PAGE', 20)
    
    @cached_property
    def widget_class(self):
        widget = super().widget_class
        return widget


artwork_chooser_viewset = ArtworkChooserViewSet("artwork_chooser")