from datetime import UTC
from datetime import datetime

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.html import escape
from django.views import View

from housegallery.images.models import CustomImage

from .forms import BulkArtworkDefaultsForm
from .forms import BulkArtworkFormSet
from .models import Artwork


class BulkAddArtworksView(View):
    template_name = "artworks/admin/bulk_add.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, defaults_form, formset, **kwargs):
        breadcrumbs_items = [
            {
                "url": reverse("wagtailsnippets_artworks_artwork:list"),
                "label": "Artworks",
            },
            {"url": "", "label": "Bulk Add"},
        ]
        return {
            "defaults_form": defaults_form,
            "formset": formset,
            "breadcrumbs_items": breadcrumbs_items,
            "header_icon": "image",
            "page_title": "Bulk Add Artworks",
            "header_title": "Bulk Add Artworks",
            **kwargs,
        }

    def get(self, request, *args, **kwargs):
        defaults_form = BulkArtworkDefaultsForm()
        formset = BulkArtworkFormSet()
        return render(
            request,
            self.template_name,
            self.get_context_data(defaults_form, formset),
        )

    def post(self, request, *args, **kwargs):
        defaults_form = BulkArtworkDefaultsForm(request.POST)
        formset = BulkArtworkFormSet(request.POST)

        if not defaults_form.is_valid() or not formset.is_valid():
            return render(
                request,
                self.template_name,
                self.get_context_data(defaults_form, formset),
            )

        action = request.POST.get("action", "draft")
        publish = action == "publish"

        # Extract defaults
        default_artists = defaults_form.cleaned_data.get("artists") or []
        default_materials_str = defaults_form.cleaned_data.get("materials", "")
        default_materials = _parse_tags(default_materials_str)
        default_date = defaults_form.cleaned_data.get("date")
        default_price = defaults_form.cleaned_data.get("price", "")

        # Filter to non-empty, non-deleted rows
        rows = [
            form
            for form in formset.forms
            if not form.cleaned_data.get("DELETE", False) and not form.is_empty()
        ]

        count = 0
        with transaction.atomic():
            for form in rows:
                data = form.cleaned_data

                # Wrap title in <p> tags with HTML escaping
                raw_title = data.get("title", "")
                title = f"<p>{escape(raw_title)}</p>" if raw_title else ""

                # Merge row values with defaults (row overrides default)
                price = data.get("price") or default_price
                row_materials_str = data.get("materials", "")
                materials = (
                    _parse_tags(row_materials_str)
                    if row_materials_str
                    else default_materials
                )

                # Build date from default if provided
                date_value = None
                if default_date:
                    date_value = datetime.combine(
                        default_date, datetime.min.time(), tzinfo=UTC,
                    )

                artwork = Artwork(
                    title=title,
                    description=data.get("description", ""),
                    size=data.get("size", ""),
                    width_inches=data.get("width_inches"),
                    height_inches=data.get("height_inches"),
                    depth_inches=data.get("depth_inches"),
                    date=date_value,
                    price=price,
                    live=False,
                )
                artwork.save()

                # Assign artists via cluster API
                for artist in default_artists:
                    artwork.artwork_artists.create(artist=artist)

                # Assign image via cluster API
                image_id = data.get("image")
                if image_id:
                    image = CustomImage.objects.get(pk=image_id)
                    artwork.artwork_images.create(image=image, sort_order=0)

                # Assign materials via ClusterTaggableManager
                if materials:
                    artwork.materials.add(*materials)

                # Save again to persist cluster children
                artwork.save()

                # Create revision
                revision = artwork.save_revision(user=request.user)
                if publish:
                    revision.publish(user=request.user)

                count += 1

        messages.success(request, f"Created {count} artworks")
        return redirect(reverse("wagtailsnippets_artworks_artwork:list"))


def _parse_tags(tag_string):
    """Parse comma-separated tag string into list of stripped, non-empty names."""
    if not tag_string:
        return []
    return [t.strip() for t in tag_string.split(",") if t.strip()]
