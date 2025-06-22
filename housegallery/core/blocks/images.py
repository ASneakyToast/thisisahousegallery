from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock


class SingleImageBlock(blocks.StructBlock):
    """
    Single image block for galleries.
    """
    image = ImageChooserBlock(required=True)
    caption = blocks.CharBlock(required=False, max_length=255, help_text="Optional caption for this image")
    
    class Meta:
        template = 'components/blocks/single_image_block.html'
        icon = 'image'
        label = 'Single Image'


class TaggedSetBlock(blocks.StructBlock):
    """
    Block that displays all images with a specific tag.
    """
    tag = blocks.CharBlock(
        required=True,
        max_length=100,
        help_text="Enter tag name to display all images with this tag"
    )
    title = blocks.CharBlock(
        required=False,
        max_length=255,
        help_text="Optional title for this set of images"
    )
    
    class Meta:
        template = 'components/blocks/tagged_set_block.html'
        icon = 'tag'
        label = 'Tagged Image Set'
    
    def get_context(self, value, parent_context=None):
        """Add images with the specified tag to the template context."""
        context = super().get_context(value, parent_context)
        tag = value.get('tag', '')
        if tag:
            from housegallery.images.models import CustomImage
            context['images'] = CustomImage.objects.filter(tags__name__iexact=tag).distinct()
        else:
            context['images'] = []
        return context


class AllImagesBlock(blocks.StructBlock):
    """
    Block that displays all images in the gallery.
    """
    limit = blocks.IntegerBlock(required=False, min_value=1, max_value=100, help_text="Maximum number of images to display (leave blank for all)")
    
    class Meta:
        template = 'components/blocks/all_images_block.html'
        icon = 'image'
        label = 'All Images'
    
    def get_context(self, value, parent_context=None):
        """Add all images to the template context."""
        context = super().get_context(value, parent_context)
        limit = value.get('limit')
        from housegallery.images.models import CustomImage
        queryset = CustomImage.objects.all()
        if limit:
            queryset = queryset[:limit]
        context['images'] = queryset
        return context


class GalleryBlock(blocks.StructBlock):
    """
    Gallery block with title, display style, and gallery items.
    """
    title = blocks.CharBlock(required=False, max_length=255, help_text="Optional title for the gallery")
    display_style = blocks.ChoiceBlock(
        choices=[
            ('columns', 'Columns'),
            ('rows', 'Rows'),
            ('scattered', 'Scattered'),
        ],
        default='columns',
        help_text="Choose how to display the gallery images"
    )
    full_width = blocks.BooleanBlock(required=False, default=False, help_text="Enable full-width layout using layout gutter spacing")
    gallery_items = blocks.StreamBlock([
        ('single_image', SingleImageBlock()),
        ('tagged_set', TaggedSetBlock()),
        ('all_images', AllImagesBlock()),
    ], help_text="Add gallery items")
    
    def get_context(self, value, parent_context=None):
        """Add display style context and random size classes for scattered layout."""
        import random
        context = super().get_context(value, parent_context)
        
        # Add display style and full_width to context
        context['display_style'] = value.get('display_style', 'columns')
        context['full_width'] = value.get('full_width', False)
        
        # For scattered layout, generate random size classes
        if context['display_style'] == 'scattered':
            # Set a seed for consistent randomization on page load
            random.seed(42)  # You could use page id or similar for more variety
            
            size_classes = ['small', 'medium', 'large']
            weights = [30, 50, 20]  # small, medium, large percentages
            
            # Generate 50 random size classes (enough for most galleries)
            random_sizes = []
            for i in range(50):
                rand_num = random.randint(1, 100)
                if rand_num <= weights[0]:  # 1-30: small
                    random_sizes.append('small')
                elif rand_num <= weights[0] + weights[1]:  # 31-80: medium
                    random_sizes.append('medium')
                else:  # 81-100: large
                    random_sizes.append('large')
            
            context['random_sizes'] = random_sizes
        
        return context
    
    class Meta:
        template = 'components/blocks/gallery_block.html'
        icon = 'image'
        label = 'Gallery'