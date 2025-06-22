# ruff: noqa
from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.decorators.vary import vary_on_headers
from django.views.generic import TemplateView

from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.utils.urlpatterns import decorate_urlpatterns

ignore_cache_urlpatterns = [
    # Custom images URLs (must come before wagtailadmin_urls to override)
    path('admin/images/', include('housegallery.images.urls')),
    path('admin/', include(wagtailadmin_urls)),
    path('djadmin/', admin.site.urls),
    path('documents/', include(wagtaildocs_urls)),
]

# Public URLs that are meant to be cached.
public_urlpatterns = [
    path('sitemap.xml', sitemap),
]

if settings.DEBUG:

    # Media files are served from GSB, shared with ccaedu-dev instances on Cloud Run
    # Serve static files from development server
    from django.conf.urls.static import static
    ignore_cache_urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # ignore_cache_urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    ignore_cache_urlpatterns += [
        # Add views for testing 404 and 500 templates
        path('test404/', TemplateView.as_view(template_name='404.html')),
        path('test500/', TemplateView.as_view(template_name='500.html')),
    ]

# Join private and public URLs.
urlpatterns = ignore_cache_urlpatterns + public_urlpatterns + [
    # Add Wagtail URLs at the end.
    # Wagtail cache-control is set on the page models's serve methods.
    path('', include(wagtail_urls)),
]
