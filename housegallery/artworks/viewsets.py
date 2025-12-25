from wagtail.snippets.views.snippets import SnippetViewSet
from django.utils.translation import gettext_lazy as _
import django_filters
from taggit.models import Tag
from .models import Artwork
from .views import ArtworkIndexView


class ArtworkFilterSet(django_filters.FilterSet):
    """Custom filterset for Artwork model that handles ClusterTaggableManager fields"""
    
    # Define a custom filter for materials
    materials = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.none(),  # Will be set in __init__
        field_name='materials',
        label=_('Materials'),
        method='filter_materials'
    )
    
    class Meta:
        model = Artwork
        fields = {
            'date': ['exact', 'year', 'year__gt', 'year__lt'],
            'artists': ['exact'],
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show tags that are actually used by artworks
        used_tags = Tag.objects.filter(
            taggit_taggeditem_items__content_type__app_label='artworks',
            taggit_taggeditem_items__content_type__model='artwork'
        ).distinct().order_by('name')
        self.filters['materials'].field.queryset = used_tags
    
    def filter_materials(self, queryset, name, value):
        """Custom filter method for materials tags"""
        if value:
            # Filter artworks that have ANY of the selected tags
            return queryset.filter(materials__in=value).distinct()
        return queryset


class ArtworkSnippetViewSet(SnippetViewSet):
    model = Artwork
    icon = "image"
    menu_label = "Artworks"
    menu_name = "artworks"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    add_to_admin_menu = False
    
    # List display configuration
    list_display = ["title_sortable", "admin_thumb", "artist_names", "date_year", "price", "date_published"]
    list_filter = ["date", "artists", "materials"]
    list_per_page = 40
    ordering = ["-date", "title"]
    filterset_class = ArtworkFilterSet
    
    # Search configuration
    search_fields = ["title", "description", "artists__name", "materials__name"]
    
    # Enable export
    list_export = ["title", "artist_names", "materials_list", "width_inches", "height_inches", "depth_inches", "size_display", "price", "date", "description"]
    
    # Custom index view class to use our filter mixin
    index_view_class = ArtworkIndexView
    
    def get_queryset(self, request=None):
        """Optimize queryset to avoid N+1 queries"""
        queryset = super().get_queryset(request)
        if queryset is not None:
            return queryset.prefetch_related('artists', 'materials', 'artwork_images__image')
        # Fallback to model's default manager if parent returns None
        return self.model.objects.prefetch_related('artists', 'materials', 'artwork_images__image')
    
    def date_year(self, obj):
        """Display just the year from the date field"""
        if obj.date:
            return obj.date.year
        return "-"
    
    date_year.short_description = "Date"
    date_year.admin_order_field = "date"