from wagtail import blocks

from housegallery.core.blocks.links import ButtonLinkBlock, ListOfLinksBlock
from housegallery.core.blocks.images import GalleryBlock


class RichTextBlock(blocks.RichTextBlock):
    """
    Rich text block with standard features.
    """
    class Meta:
        template = 'components/blocks/rich_text_block.html'
        icon = 'doc-full'
        label = 'Rich Text'


class BlankStreamBlock(blocks.StreamBlock):
    class Meta:
        template = 'components/streamfields/generic_stream_block.html'

    rich_text = RichTextBlock(
        label='Rich Text',
        icon='doc-full'
    )

    gallery = GalleryBlock(
        label='Gallery',
        icon='image'
    )

    button_link = ButtonLinkBlock(
        label=('Single button'),
        icon='link'
    )

    list_of_links = ListOfLinksBlock(
        label='List of Links',
        icon='list-ul'
    )