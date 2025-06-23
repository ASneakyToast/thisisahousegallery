from functools import cached_property

from django import forms
from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models import Q, F
from django.utils.translation import gettext_lazy as _
from wagtail.admin.forms.choosers import BaseFilterForm, LocaleFilterMixin
from wagtail.admin.ui.tables import TitleColumn, Column
from wagtail.admin.views.generic.chooser import (BaseChooseView,
                                                 ChooseResultsViewMixin,
                                                 ChooseViewMixin,
                                                 CreationFormMixin)
from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.models import TranslatableMixin


class ExhibitionImageSearchFilterMixin(forms.Form):
    """Search filter mixin for CustomImage model with exhibition-focused filters."""
    
    q = forms.CharField(
        label=_("Search term"),
        widget=forms.TextInput(attrs={"placeholder": _("Search images by title, description, or alt text...")}),
        required=False,
    )
    
    tags = forms.MultipleChoiceField(
        label=_("Tags"),
        widget=forms.SelectMultiple(attrs={
            "class": "form-control",
            "size": "6",
            "style": "height: auto;"
        }),
        required=False,
        help_text=_("Select one or more tags to filter images.")
    )
    
    credit = forms.CharField(
        label=_("Credit/Photographer"),
        widget=forms.TextInput(attrs={
            "placeholder": _("Search by photographer or credit..."),
            "class": "form-control"
        }),
        required=False,
    )
    
    orientation = forms.ChoiceField(
        label=_("Orientation"),
        required=False,
        choices=[
            ('', _('All orientations')),
            ('portrait', _('Portrait (taller than wide)')),
            ('landscape', _('Landscape (wider than tall)')),
            ('square', _('Square (equal width and height)')),
        ],
        widget=forms.Select(attrs={"class": "form-select"})
    )
    
    file_size = forms.ChoiceField(
        label=_("File Size"),
        required=False,
        choices=[
            ('', _('All sizes')),
            ('small', _('Small (< 1MB)')),
            ('medium', _('Medium (1-5MB)')),
            ('large', _('Large (> 5MB)')),
        ],
        widget=forms.Select(attrs={"class": "form-select"})
    )
    
    date_from = forms.DateField(
        label=_("Uploaded from"),
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    
    date_to = forms.DateField(
        label=_("Uploaded to"),
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    
    has_description = forms.BooleanField(
        label=_("Has description"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text=_("Show only images with descriptions")
    )
    
    submit = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "type": "submit",
            "value": _("Filter"),
            "class": "button",
            "style": "margin-top: 10px;"
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate tag choices dynamically from available tags
        from taggit.models import Tag
        available_tags = Tag.objects.all().order_by('name')
        tag_choices = [(tag.name, tag.name) for tag in available_tags]
        self.fields['tags'].choices = tag_choices
        
        # Add data attribute for JavaScript identification
        self.helper_attrs = {'data-chooser-filter': 'exhibition-image'}

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        # Validate date range
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError(_('Uploaded from date must be before uploaded to date.'))
        
        return cleaned_data

    def filter(self, objects):
        # Apply base filtering (if any parent class has filter method)
        
        # Text search across multiple fields
        search_query = self.cleaned_data.get("q")
        if search_query:
            objects = objects.filter(
                Q(title__icontains=search_query) |
                Q(alt__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(credit__icontains=search_query)
            )
            self.is_searching = True
            self.search_query = search_query
            
        # Tag filtering with multi-select
        tags_filter = self.cleaned_data.get("tags")
        if tags_filter:
            # tags_filter is now a list of selected tag names
            objects = objects.filter(tags__name__in=tags_filter).distinct()
            
        # Credit filtering
        credit_filter = self.cleaned_data.get("credit")
        if credit_filter:
            objects = objects.filter(credit__icontains=credit_filter)
            
        # Orientation filtering
        orientation_filter = self.cleaned_data.get("orientation")
        if orientation_filter:
            if orientation_filter == 'portrait':
                objects = objects.filter(height__gt=F('width'))
            elif orientation_filter == 'landscape':
                objects = objects.filter(width__gt=F('height'))
            elif orientation_filter == 'square':
                objects = objects.filter(width=F('height'))
                
        # File size filtering
        file_size_filter = self.cleaned_data.get("file_size")
        if file_size_filter:
            if file_size_filter == 'small':
                objects = objects.filter(file_size__lt=1024*1024)  # < 1MB
            elif file_size_filter == 'medium':
                objects = objects.filter(
                    file_size__gte=1024*1024,  # >= 1MB
                    file_size__lt=5*1024*1024  # < 5MB
                )
            elif file_size_filter == 'large':
                objects = objects.filter(file_size__gte=5*1024*1024)  # >= 5MB
            
        # Date range filtering
        date_from = self.cleaned_data.get("date_from")
        if date_from:
            objects = objects.filter(created_at__gte=date_from)
            
        date_to = self.cleaned_data.get("date_to")
        if date_to:
            objects = objects.filter(created_at__lte=date_to)
            
        # Description filtering
        has_description = self.cleaned_data.get("has_description")
        if has_description:
            objects = objects.exclude(Q(description='') | Q(description__isnull=True))
            
        return objects


class BaseExhibitionImageChooseView(BaseChooseView):
    """Base chooser view for CustomImage model with exhibition-focused columns."""
    ordering = ["-created_at"]
    
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
                name="preview",
                label=_("Preview"),
                accessor=lambda obj: obj.get_rendition('fill-100x100').url if obj else '',
            ),
            Column(
                name="credit",
                label=_("Credit"),
                accessor=lambda obj: obj.credit or '-',
            ),
            Column(
                name="tags",
                label=_("Tags"),
                accessor=lambda obj: ', '.join([tag.name for tag in obj.tags.all()]) or '-',
            ),
            Column(
                name="file_size",
                label=_("Size"),
                accessor=lambda obj: f"{obj.file_size / (1024*1024):.1f}MB" if obj.file_size else '-',
            ),
            Column(
                name="dimensions",
                label=_("Dimensions"),
                accessor=lambda obj: f"{obj.width}×{obj.height}" if obj.width and obj.height else '-',
            ),
            Column(
                name="created_at",
                label=_("Uploaded"),
                accessor=lambda obj: obj.created_at.strftime('%Y-%m-%d') if obj.created_at else '-',
            ),
        ]

    def get_filter_form_class(self):
        bases = [ExhibitionImageSearchFilterMixin, BaseFilterForm]

        i18n_enabled = getattr(settings, "WAGTAIL_I18N_ENABLED", False)
        if i18n_enabled and issubclass(self.model_class, TranslatableMixin):
            bases.insert(0, LocaleFilterMixin)

        return type(
            "FilterForm",
            tuple(bases),
            {},
        )


class ExhibitionImageChooseView(ChooseViewMixin, CreationFormMixin, BaseExhibitionImageChooseView):
    pass


class ExhibitionImageChooseResultsView(ChooseResultsViewMixin, CreationFormMixin, BaseExhibitionImageChooseView):
    pass


class ExhibitionImageChooserViewSet(ChooserViewSet):
    model = 'images.CustomImage'

    choose_view_class = ExhibitionImageChooseView
    choose_results_view_class = ExhibitionImageChooseResultsView

    icon = "image"
    choose_one_text = _("Choose an image")
    choose_another_text = _("Choose another image")
    
    # Enable multi-select for use with MultipleChooserPanel
    # This allows the chooser to work with existing MultipleChooserPanel implementations
    
    @cached_property
    def widget_class(self):
        widget = super().widget_class
        # Customize widget if needed for exhibition-specific functionality
        return widget


exhibition_image_chooser_viewset = ExhibitionImageChooserViewSet("exhibition_image_chooser")