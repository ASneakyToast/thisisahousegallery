from wagtail import blocks

from housegallery.core.rich_text import MINIMAL_RICHTEXT
from housegallery.core.blocks.links import ButtonLinkBlock, CarrotLinkBlock


class HeroSection(blocks.StructBlock):
    intro = blocks.RichTextBlock(
        required=True,
        features=MINIMAL_RICHTEXT,
        max_length=128,
        verbose_name='Welcome doormatt message',
        help_text='Introduction | Recommended: 10-15 words | Max length: 128 characters.'
    )

    ctas = blocks.StreamBlock([
        ('link_button', ButtonLinkBlock()),
        ('link_carrot', CarrotLinkBlock()),
    ],
        help_text='Add some major links bro',
        icon='link'
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
