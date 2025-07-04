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
        
        # Get exhibition pages and their showcase images
        exhibition_data = []
        exhibitions = value.get('exhibitions', [])
        
        for exhibition_page in exhibitions:
            if exhibition_page and hasattr(exhibition_page, 'specific'):
                exhibition = exhibition_page.specific
                
                # Get the first showcard image from the exhibition
                showcase_image = None
                if hasattr(exhibition, 'get_first_showcard_image'):
                    showcase_image = exhibition.get_first_showcard_image()
                elif hasattr(exhibition, 'get_first_gallery_image'):
                    # Fallback to first gallery image if no showcard method
                    first_image_data = exhibition.get_first_gallery_image()
                    if first_image_data:
                        showcase_image = first_image_data.get('image')
                
                exhibition_data.append({
                    'page': exhibition,
                    'title': exhibition.title,
                    'url': exhibition.url,
                    'showcase_image': showcase_image,
                    'date': getattr(exhibition, 'get_formatted_date_short', lambda: '')(),
                    'artists': getattr(exhibition, 'artists', []),
                })
        
        context['exhibition_data'] = exhibition_data
        context['auto_scroll'] = value.get('auto_scroll', False)
        context['scroll_speed'] = value.get('scroll_speed', 'medium')
        
        return context
    
    class Meta:
        template = 'components/blocks/horizontal_features_block.html'
        icon = 'arrow-right'
        label = 'Horizontal Features'