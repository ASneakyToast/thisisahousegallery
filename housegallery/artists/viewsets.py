import django_filters
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from wagtail.snippets.views.snippets import SnippetViewSet
from .models import Artist
from .views import ArtistIndexView


class ArtistFilterSet(django_filters.FilterSet):
    """Custom filterset for Artist model with simple, working filters"""
    
    class Meta:
        model = Artist
        fields = {
            'birth_year': ['exact', 'gte', 'lte'],
        }


class ArtistSnippetViewSet(SnippetViewSet):
    model = Artist
    icon = "user"
    menu_label = "Artists"
    menu_name = "artists"
    menu_order = 100
    add_to_settings_menu = False
    exclude_from_explorer = False
    add_to_admin_menu = False
    
    # List display configuration
    list_display = ["name_sortable", "email", "artwork_count"]
    list_filter = ["birth_year"]
    list_per_page = 100
    ordering = ["name"]
    
    # Search configuration
    search_fields = ["name", "bio"]
    
    # Enable export
    list_export = ["name", "email", "birth_year", "bio", "website", "artwork_count"]
    
    # Custom filterset and index view
    filterset_class = ArtistFilterSet
    index_view_class = ArtistIndexView
    
    def get_queryset(self, request=None):
        """Optimize queryset to avoid N+1 queries and add artwork count annotation"""
        queryset = super().get_queryset(request)
        if queryset is not None:
            return queryset.prefetch_related('artwork_list').select_related('profile_image').annotate(
                artwork_count_annotated=Count('artwork_list')
            )
        # Fallback to model's default manager if parent returns None
        return self.model.objects.prefetch_related('artwork_list').select_related('profile_image').annotate(
            artwork_count_annotated=Count('artwork_list')
        )