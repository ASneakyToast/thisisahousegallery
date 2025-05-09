from wagtail import blocks

from housegallery.core.rich_text import MINIMAL_RICHTEXT
from housegallery.core.blocks.links import ButtonLinkBlock, CarrotLinkBlock, ListOfLinksBlock

# Create a subclass of ListOfLinksBlock that hides the title field in the admin
class HeroLinksBlock(ListOfLinksBlock):
    """A collection of links for the hero section with the title field hidden."""

    # Override the title field to make it not required and hide it in the admin
    title = None  # This removes the field entirely




class HeroSection(blocks.StructBlock):
    intro = blocks.RichTextBlock(
        required=True,
        features=MINIMAL_RICHTEXT,
        max_length=128,
        verbose_name='Welcome doormatt message',
        help_text='Introduction | Recommended: 10-15 words | Max length: 128 characters.'
    )

    ctas = HeroLinksBlock(
        required=False,
        label='Call to Actions',
        help_text='Add links for the hero section'
    )

    class Meta:
        template = 'components/home/hero-section.html'
        verbose_name = 'Hero Section'
        icon = 'table'

'''
class ScatteredImagesBlock(blocks.StructBlock):
    image_tag
'''


class HomeStreamBlock(blocks.StreamBlock):
    class Meta:
        template = 'components/streamfields/generic_stream_block.html'

    hero = HeroSection()
