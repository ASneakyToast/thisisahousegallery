"""
Shared image URL utility functions.

Centralises rendition-URL generation logic so that ExhibitionPage,
KioskPage, and any future consumers share a single code path.
"""


def _find_rendition_in_prefetch(image_obj, filter_spec):
    """Check prefetched renditions for matching filter_spec. Returns rendition or None."""
    try:
        for rendition in image_obj.renditions.all():
            if rendition.filter_spec == filter_spec:
                return rendition
    except Exception:
        pass
    return None


def get_image_urls(image_obj, specs=None):
    """
    Get standardized image URL dict for a single image.

    Checks prefetched renditions first to avoid DB queries.
    Falls back to get_rendition() if rendition not in prefetch cache.

    Returns dict with keys: thumb_url, medium_url, full_url,
    original_url, width, height, alt, credit, title
    """
    if specs is None:
        specs = {
            "thumb": "width-400",
            "medium": "width-800|format-webp",
            "full": "width-1440|format-webp|webpquality-85",
        }

    urls = {}
    for key, filter_spec in specs.items():
        rendition = _find_rendition_in_prefetch(image_obj, filter_spec)
        if rendition is None:
            try:
                rendition = image_obj.get_rendition(filter_spec)
            except Exception:
                rendition = None
        urls[f"{key}_url"] = rendition.url if rendition else ""

    # Original file URL
    try:
        urls["original_url"] = image_obj.file.url
    except Exception:
        urls["original_url"] = urls.get("full_url", "")

    # Image metadata
    urls["width"] = image_obj.width
    urls["height"] = image_obj.height
    urls["alt"] = getattr(image_obj, "alt", "") or image_obj.title or ""
    urls["credit"] = getattr(image_obj, "credit", "") or ""
    urls["title"] = image_obj.title or ""

    return urls


def get_image_urls_batch(image_objects, specs=None):
    """
    Batch get image URLs for multiple images with minimal DB queries.

    Pre-fetches all needed renditions in a single query, then calls
    get_image_urls() for each image (which finds renditions in prefetch cache).

    Returns list of dicts in same order as input.
    """
    from housegallery.images.models import Rendition

    if specs is None:
        specs = {
            "thumb": "width-400",
            "medium": "width-800|format-webp",
            "full": "width-1440|format-webp|webpquality-85",
        }

    if not image_objects:
        return []

    # Collect all image PKs
    images_list = list(image_objects)
    image_pks = [img.pk for img in images_list]
    filter_specs = list(specs.values())

    # Batch fetch all needed renditions in one query
    renditions = Rendition.objects.filter(
        image_id__in=image_pks,
        filter_spec__in=filter_specs,
    ).select_related("image")

    # Build lookup: {image_pk: {filter_spec: rendition}}
    rendition_map = {}
    for r in renditions:
        rendition_map.setdefault(r.image_id, {})[r.filter_spec] = r

    # Inject prefetched renditions into each image's cache
    for img in images_list:
        img_renditions = rendition_map.get(img.pk, {})
        # Set up a fake prefetch cache so _find_rendition_in_prefetch works
        if not hasattr(img, '_prefetched_objects_cache'):
            img._prefetched_objects_cache = {}
        img._prefetched_objects_cache['renditions'] = list(img_renditions.values())

    return [get_image_urls(img, specs) for img in images_list]
