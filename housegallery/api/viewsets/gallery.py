from django.db.models import Prefetch
from rest_framework import viewsets, filters
from housegallery.artworks.models import Artwork, ArtworkImage
from housegallery.images.models import CustomImage
from housegallery.api.serializers import ArtworkSerializer, ArtworkListSerializer, ImageSerializer
from housegallery.api.authentication.readonly_token import ReadOnlyTokenAuthentication
from housegallery.api.permissions.readonly_token import ReadOnlyTokenPermission


class GalleryArtworkViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to all artworks, authenticated via ReadOnlyToken.

    Filters: ?artist=, ?materials=, ?search=, ?ids=
    """

    authentication_classes = [ReadOnlyTokenAuthentication]
    permission_classes = [ReadOnlyTokenPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['date', 'id']
    ordering = ['-date', '-id']

    def get_serializer_class(self):
        if self.action == 'list':
            return ArtworkListSerializer
        return ArtworkSerializer

    def get_queryset(self):
        queryset = Artwork.objects.prefetch_related(
            'artists',
            'materials',
            Prefetch(
                'artwork_images',
                queryset=ArtworkImage.objects.select_related('image').order_by('sort_order')
            ),
        ).distinct()

        params = self.request.query_params

        # Filter by artist ID
        artist = params.get('artist')
        if artist:
            queryset = queryset.filter(artists__id=artist)

        # Filter by materials
        materials = params.get('materials')
        if materials:
            material_list = [m.strip() for m in materials.split(',')]
            queryset = queryset.filter(materials__name__in=material_list).distinct()

        # Filter by specific IDs
        ids = params.get('ids')
        if ids:
            id_list = [i.strip() for i in ids.split(',') if i.strip().isdigit()]
            if id_list:
                queryset = queryset.filter(id__in=id_list)

        return queryset


class GalleryImageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to all images, authenticated via ReadOnlyToken.

    Filters: ?tag=, ?ids=
    """

    serializer_class = ImageSerializer
    authentication_classes = [ReadOnlyTokenAuthentication]
    permission_classes = [ReadOnlyTokenPermission]

    def get_queryset(self):
        queryset = CustomImage.objects.all()

        params = self.request.query_params

        # Filter by Wagtail image tag
        tag = params.get('tag')
        if tag:
            queryset = queryset.filter(tags__name=tag)

        # Filter by specific IDs
        ids = params.get('ids')
        if ids:
            id_list = [i.strip() for i in ids.split(',') if i.strip().isdigit()]
            if id_list:
                queryset = queryset.filter(id__in=id_list)

        return queryset
