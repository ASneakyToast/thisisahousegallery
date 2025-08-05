from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from housegallery.api.viewsets import ArtistViewSet, ArtworkViewSet, ImageViewSet

app_name = 'api'

# Create router for v1 API
router_v1 = DefaultRouter()
router_v1.register(r'artists', ArtistViewSet, basename='artist')
router_v1.register(r'artworks', ArtworkViewSet, basename='artwork')
router_v1.register(r'images', ImageViewSet, basename='image')

urlpatterns = [
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),
    
    # API v1
    path('v1/', include(router_v1.urls)),
]