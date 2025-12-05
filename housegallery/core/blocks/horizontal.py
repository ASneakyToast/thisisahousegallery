from wagtail import blocks
from wagtail.blocks import PageChooserBlock


class HorizontalFeaturesBlock(blocks.StructBlock):
    """
    Horizontal scrolling block for showcasing exhibitions in a Netflix-style layout.
    """
    title = blocks.CharBlock(
        required=False,
        max_length=255,
        help_text="Optional title for the horizontal features section"
    )

    auto_scroll = blocks.BooleanBlock(
        required=False,
        default=False,
        help_text="Enable automatic horizontal scrolling"
    )

    scroll_speed = blocks.ChoiceBlock(
        choices=[
            ('slow', 'Slow'),
            ('medium', 'Medium'),
            ('fast', 'Fast'),
        ],
        default='medium',
        help_text="Speed of automatic scrolling (if enabled)"
    )

    exhibitions = blocks.ListBlock(
        PageChooserBlock(
            'exhibitions.ExhibitionPage',
            help_text="Select exhibitions to display in the horizontal scroll"
        ),
        help_text="Choose exhibitions to feature in the horizontal scroll"
    )

    def get_context(self, value, parent_context=None):
        """Add exhibition data and showcards to the template context."""
        context = super().get_context(value, parent_context)

        exhibitions = value.get('exhibitions', [])
        if not exhibitions:
            context['exhibition_data'] = []
            context['auto_scroll'] = value.get('auto_scroll', False)
            context['scroll_speed'] = value.get('scroll_speed', 'medium')
            return context

        # Collect page IDs for bulk query
        page_ids = [p.id for p in exhibitions if p]

        if not page_ids:
            context['exhibition_data'] = []
            context['auto_scroll'] = value.get('auto_scroll', False)
            context['scroll_speed'] = value.get('scroll_speed', 'medium')
            return context

        # Import here to avoid circular imports
        from housegallery.exhibitions.models import ExhibitionPage

        # Fetch all exhibitions with optimized prefetching in ONE query
        optimized_exhibitions = ExhibitionPage.objects.filter(
            id__in=page_ids
        ).select_related(
            # No direct FK fields to select_related on ExhibitionPage
        ).prefetch_related(
            # Prefetch showcard photos with images
            "showcard_photos__image",
            # Prefetch artists through the through table
            "exhibition_artists__artist",
        )

        # Create a lookup dict for O(1) access
        exhibition_map = {e.id: e for e in optimized_exhibitions}

        # Build exhibition data maintaining the original order
        exhibition_data = []
        for page in exhibitions:
            if not page:
                continue

            exhibition = exhibition_map.get(page.id)
            if not exhibition:
                continue

            # Get first showcard image from prefetched data (no extra query)
            showcase_image = None
            showcard_photos = list(exhibition.showcard_photos.all()[:1])
            if showcard_photos:
                showcase_image = showcard_photos[0].image

            # Get artists from prefetched data (no extra query)
            artists = [ea.artist for ea in exhibition.exhibition_artists.all()]

            exhibition_data.append({
                'page': exhibition,
                'title': exhibition.title,
                'url': exhibition.url,
                'showcase_image': showcase_image,
                'date': exhibition.get_formatted_date_short() if hasattr(exhibition, 'get_formatted_date_short') else '',
                'artists': artists,
            })

        context['exhibition_data'] = exhibition_data
        context['auto_scroll'] = value.get('auto_scroll', False)
        context['scroll_speed'] = value.get('scroll_speed', 'medium')

        return context

    class Meta:
        template = 'components/blocks/horizontal_features_block.html'
        icon = 'arrow-right'
        label = 'Horizontal Features'
