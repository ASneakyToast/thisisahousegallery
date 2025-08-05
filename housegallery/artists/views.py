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
from wagtail.snippets.views.snippets import IndexView
from wagtail.admin.forms.search import SearchForm
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


class ArtistSearchFilterMixin(forms.Form):
    """Search filter mixin for Artist model with artist-focused filters."""
    
    q = forms.CharField(
        label=_("Search term"),
        widget=forms.TextInput(attrs={"placeholder": _("Search artists by name or bio...")}),
        required=False,
    )
    
    birth_year_from = forms.IntegerField(
        label=_("Birth year from"),
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 1950"})
    )
    
    birth_year_to = forms.IntegerField(
        label=_("Birth year to"),
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 2000"})
    )
    
    has_website = forms.BooleanField(
        label=_("Has website"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text=_("Show only artists with websites")
    )
    
    has_bio = forms.BooleanField(
        label=_("Has bio"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text=_("Show only artists with biographies")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        birth_year_from = cleaned_data.get('birth_year_from')
        birth_year_to = cleaned_data.get('birth_year_to')
        
        # Validate birth year range
        if birth_year_from and birth_year_to and birth_year_from > birth_year_to:
            raise forms.ValidationError(_('Birth year from must be before birth year to.'))
        
        return cleaned_data

    def filter(self, objects):
        # Text search across multiple fields
        search_query = self.cleaned_data.get("q")
        if search_query:
            objects = objects.filter(
                Q(name__icontains=search_query) |
                Q(bio__icontains=search_query)
            ).distinct()
            
        # Birth year range filtering
        birth_year_from = self.cleaned_data.get("birth_year_from")
        if birth_year_from:
            objects = objects.filter(birth_year__gte=birth_year_from)
            
        birth_year_to = self.cleaned_data.get("birth_year_to")
        if birth_year_to:
            objects = objects.filter(birth_year__lte=birth_year_to)
            
        # Website filtering
        has_website = self.cleaned_data.get("has_website")
        if has_website:
            objects = objects.exclude(Q(website='') | Q(website__isnull=True))
            
        # Bio filtering
        has_bio = self.cleaned_data.get("has_bio")
        if has_bio:
            objects = objects.exclude(Q(bio='') | Q(bio__isnull=True))
            
        return objects


class BaseArtistChooseView(BaseChooseView):
    """Base chooser view for Artist model with artist-focused columns."""
    ordering = ["name"]  # Sort by name alphabetically
    
    def get_queryset(self):
        """Optimize queryset to avoid N+1 queries"""
        return super().get_queryset().prefetch_related('artwork_list')
    
    @property
    def columns(self):
        return [
            TitleColumn(
                name="name",
                label=_("Name"),
                url_name=self.chosen_url_name,
                link_attrs={"data-chooser-modal-choice": True},
            ),
            Column(
                name="birth_year",
                label=_("Birth Year"),
                accessor=lambda obj: obj.birth_year or '-',
            ),
            Column(
                name="bio_preview",
                label=_("Bio"),
                accessor=lambda obj: (obj.bio[:50] + '...') if len(obj.bio or '') > 50 else (obj.bio or '-'),
            ),
            Column(
                name="website",
                label=_("Website"),
                accessor=lambda obj: format_html(
                    '<a href="{}" target="_blank" rel="noopener">Website</a>', 
                    obj.website
                ) if obj.website else '-',
            ),
            Column(
                name="artwork_count",
                label=_("Artworks"),
                accessor=lambda obj: obj.artwork_list.count(),
            ),
        ]

    def get_filter_form_class(self):
        bases = [ArtistSearchFilterMixin, BaseFilterForm]

        i18n_enabled = getattr(settings, "WAGTAIL_I18N_ENABLED", False)
        if i18n_enabled and issubclass(self.model_class, TranslatableMixin):
            bases.insert(0, LocaleFilterMixin)

        return type(
            "FilterForm",
            tuple(bases),
            {},
        )


class ArtistChooseView(ChooseViewMixin, CreationFormMixin, BaseArtistChooseView):
    pass


class ArtistChooseResultsView(ChooseResultsViewMixin, CreationFormMixin, BaseArtistChooseView):
    pass


class ArtistChooserViewSet(ChooserViewSet):
    model = 'artists.Artist'

    choose_view_class = ArtistChooseView
    choose_results_view_class = ArtistChooseResultsView

    icon = "user"
    choose_one_text = _("Choose an artist")
    choose_another_text = _("Choose another artist")
    paginate_by = getattr(settings, 'DEFAULT_PER_PAGE', 20)
    
    @cached_property
    def widget_class(self):
        widget = super().widget_class
        return widget


artist_chooser_viewset = ArtistChooserViewSet("artist_chooser")


@method_decorator(never_cache, name='dispatch')
class ArtistIndexView(IndexView):
    """Custom index view for Artist snippets with advanced filtering"""
    
    def get_filters(self):
        """Add custom filters to the index view"""
        filters = super().get_filters()
        
        # Add custom filter form
        filter_form = self.get_filter_form()
        if filter_form:
            filters['custom'] = filter_form
        
        return filters
    
    def get_filter_form(self):
        """Get the custom filter form instance"""
        if hasattr(self, '_filter_form'):
            return self._filter_form
            
        FilterForm = self.get_filter_form_class()
        self._filter_form = FilterForm(self.request.GET or None)
        return self._filter_form
    
    def get_filter_form_class(self):
        """Use our existing ArtistSearchFilterMixin"""
        
        class ArtistAdminFilterForm(ArtistSearchFilterMixin, SearchForm):
            """Combine artist filters with Wagtail's search form"""
            
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Remove the duplicate 'q' field from SearchForm if it exists
                if 'q' in self.fields and hasattr(ArtistSearchFilterMixin, 'q'):
                    # Keep the ArtistSearchFilterMixin version of 'q'
                    search_form_q = self.fields.pop('q', None)
        
        return ArtistAdminFilterForm
    
    def get_queryset(self):
        """Apply custom filtering to queryset"""
        queryset = super().get_queryset()
        
        # Apply custom filters
        filter_form = self.get_filter_form()
        if filter_form and filter_form.is_valid():
            queryset = filter_form.filter(queryset)
        
        return queryset