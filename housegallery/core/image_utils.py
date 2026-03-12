"""Shared image URL utilities for responsive images with srcset support."""


def _find_rendition_in_prefetch(image_obj, filter_spec):
    """Check prefetched renditions for a matching filter spec.

    Returns the rendition object if found in prefetch cache, None otherwise.
    """
    try:
        renditions = list(image_obj.renditions.all())
        for rendition in renditions:
            if rendition.filter_spec == filter_spec:
                return rendition
    except Exception:
        pass
    return None


def get_image_urls(image_obj, specs=None):
    """Get image URLs at multiple sizes with optional srcset generation.

    Args:
        image_obj: A Wagtail image instance (e.g. CustomImage).
        specs: Optional dict mapping size names to Wagtail filter specs.
               Defaults to thumb/medium/full for responsive srcset.

    Returns:
        Dict with ``{key}_url`` for each spec, plus ``original_url``,
        ``srcset``, ``sizes``, ``width``, ``height``, ``alt``, ``credit``,
        and ``title``.
    """
    if specs is None:
        specs = {
            "thumb": "width-400",
            "medium": "width-800|format-webp",
            "full": "width-1440|format-webp|webpquality-85",
        }

    urls = {}
    rendition_data = {}  # Store rendition objects for srcset generation
    for key, filter_spec in specs.items():
        rendition = _find_rendition_in_prefetch(image_obj, filter_spec)
        if rendition is None:
            try:
                rendition = image_obj.get_rendition(filter_spec)
            except Exception:
                rendition = None
        urls[f"{key}_url"] = rendition.url if rendition else ""
        if rendition:
            rendition_data[key] = rendition

    # Original file URL
    try:
        urls["original_url"] = image_obj.file.url
    except Exception:
        urls["original_url"] = urls.get("full_url", "")

    # Build srcset if we have multiple sizes
    srcset_parts = []
    if "thumb" in rendition_data:
        srcset_parts.append(f"{rendition_data['thumb'].url} {rendition_data['thumb'].width}w")
    if "medium" in rendition_data:
        srcset_parts.append(f"{rendition_data['medium'].url} {rendition_data['medium'].width}w")
    if "full" in rendition_data:
        srcset_parts.append(f"{rendition_data['full'].url} {rendition_data['full'].width}w")

    urls["srcset"] = ", ".join(srcset_parts) if len(srcset_parts) > 1 else ""
    urls["sizes"] = "(max-width: 600px) 400px, (max-width: 1200px) 800px, 1440px" if urls["srcset"] else ""

    # Image metadata
    urls["width"] = image_obj.width
    urls["height"] = image_obj.height
    urls["alt"] = getattr(image_obj, "alt", "") or image_obj.title or ""
    urls["credit"] = getattr(image_obj, "credit", "") or ""
    urls["title"] = image_obj.title or ""

    return urls


def get_image_urls_batch(image_objects, specs=None):
    """Get image URLs for multiple images, batch-loading missing renditions.

    More efficient than calling ``get_image_urls`` per image because it
    pre-fetches renditions for the whole batch in a single query.

    Args:
        image_objects: Iterable of Wagtail image instances.
        specs: Optional dict mapping size names to Wagtail filter specs.

    Returns:
        List of dicts (same structure as ``get_image_urls``), in input order.
    """
    if specs is None:
        specs = {
            "thumb": "width-400",
            "medium": "width-800|format-webp",
            "full": "width-1440|format-webp|webpquality-85",
        }

    images = list(image_objects)
    if not images:
        return []

    # Batch-load existing renditions for all images + specs in one query
    from wagtail.images.models import AbstractRendition
    rendition_model = type(images[0]).get_rendition_model()
    filter_specs = list(specs.values())
    image_pks = [img.pk for img in images]

    existing = rendition_model.objects.filter(
        image_id__in=image_pks,
        filter_spec__in=filter_specs,
    ).select_related("image")

    # Build lookup: (image_pk, filter_spec) -> rendition
    lookup = {}
    for rendition in existing:
        lookup[(rendition.image_id, rendition.filter_spec)] = rendition

    # Attach prefetched renditions so get_image_urls finds them
    for img in images:
        matched = [r for r in existing if r.image_id == img.pk]
        # Populate the prefetch cache
        img.renditions._result_cache = matched  # noqa: SLF001

    return [get_image_urls(img, specs) for img in images]
