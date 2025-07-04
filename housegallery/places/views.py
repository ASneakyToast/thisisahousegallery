from functools import cached_property

from django import forms
from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models import Q
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


class PlaceSearchFilterMixin(forms.Form):
    """Search filter mixin for Place model with place-focused filters."""
    
    q = forms.CharField(
        label=_("Search term"),
        widget=forms.TextInput(attrs={"placeholder": _("Search places by name, address, or maintainers...")}),
        required=False,
    )
    
    is_currently_operating = forms.BooleanField(
        label=_("Currently operating"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text=_("Show only places that are currently operating")
    )
    
    has_images = forms.BooleanField(
        label=_("Has images"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text=_("Show only places with images")
    )
    
    start_year_from = forms.IntegerField(
        label=_("Started from year"),
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 2000"})
    )
    
    start_year_to = forms.IntegerField(
        label=_("Started to year"),
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 2020"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        start_year_from = cleaned_data.get('start_year_from')
        start_year_to = cleaned_data.get('start_year_to')
        
        # Validate year range
        if start_year_from and start_year_to and start_year_from > start_year_to:
            raise forms.ValidationError(_('Start year from must be before start year to.'))
        
        return cleaned_data

    def filter(self, objects):
        from django.utils import timezone
        
        # Text search across multiple fields
        search_query = self.cleaned_data.get("q")
        if search_query:
            objects = objects.filter(
                Q(title__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(maintainers__name__icontains=search_query)
            ).distinct()
            
        # Currently operating filter
        is_currently_operating = self.cleaned_data.get("is_currently_operating")
        if is_currently_operating:
            today = timezone.now().date()
            # Include places with no start date OR start date <= today
            # AND no end date OR end date >= today
            objects = objects.filter(
                Q(start_date__isnull=True) | Q(start_date__lte=today)
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=today)
            )
            
        # Has images filter
        has_images = self.cleaned_data.get("has_images")
        if has_images:
            objects = objects.filter(place_images__isnull=False).distinct()
            
        # Start year range filtering (exclude places with no start date)
        start_year_from = self.cleaned_data.get("start_year_from")
        if start_year_from:
            objects = objects.filter(start_date__isnull=False, start_date__year__gte=start_year_from)
            
        start_year_to = self.cleaned_data.get("start_year_to")
        if start_year_to:
            objects = objects.filter(start_date__isnull=False, start_date__year__lte=start_year_to)
            
        return objects


class BasePlaceChooseView(BaseChooseView):
    """Base chooser view for Place model with place-focused columns."""
    ordering = ["-start_date", "title"]  # Sort by most recent first, then by name
    
    def get_queryset(self):
        """Optimize queryset to avoid N+1 queries"""
        return super().get_queryset().prefetch_related('place_images')
    
    @property
    def columns(self):
        return [
            TitleColumn(
                name="title",
                label=_("Name"),
                url_name=self.chosen_url_name,
                link_attrs={"data-chooser-modal-choice": True},
            ),
            Column(
                name="operating_period",
                label=_("Operating Period"),
                accessor=lambda obj: obj.operating_period,
            ),
            Column(
                name="maintainers",
                label=_("Maintainers"),
                accessor=lambda obj: obj.maintainer_names if obj.maintainer_names else '-',
            ),
            Column(
                name="address_preview",
                label=_("Address"),
                accessor=lambda obj: (obj.address[:50] + '...') if len(obj.address or '') > 50 else (obj.address or '-'),
            ),
            Column(
                name="status",
                label=_("Status"),
                accessor=lambda obj: "Operating" if obj.is_currently_operating else "Closed",
            ),
            Column(
                name="images_count",
                label=_("Images"),
                accessor=lambda obj: obj.place_images.count(),
            ),
        ]

    def get_filter_form_class(self):
        bases = [PlaceSearchFilterMixin, BaseFilterForm]

        i18n_enabled = getattr(settings, "WAGTAIL_I18N_ENABLED", False)
        if i18n_enabled and issubclass(self.model_class, TranslatableMixin):
            bases.insert(0, LocaleFilterMixin)

        return type(
            "FilterForm",
            tuple(bases),
            {},
        )


class PlaceChooseView(ChooseViewMixin, CreationFormMixin, BasePlaceChooseView):
    pass


class PlaceChooseResultsView(ChooseResultsViewMixin, CreationFormMixin, BasePlaceChooseView):
    pass


class PlaceChooserViewSet(ChooserViewSet):
    model = 'places.Place'

    choose_view_class = PlaceChooseView
    choose_results_view_class = PlaceChooseResultsView

    icon = "home"
    choose_one_text = _("Choose a place")
    choose_another_text = _("Choose another place")
    paginate_by = getattr(settings, 'DEFAULT_PER_PAGE', 20)
    
    @cached_property
    def widget_class(self):
        widget = super().widget_class
        return widget


place_chooser_viewset = PlaceChooserViewSet("place_chooser")