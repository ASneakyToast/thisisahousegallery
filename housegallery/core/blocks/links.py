from wagtail import blocks

from housegallery.core.utils import LinkBlock


class ButtonLinkBlock(LinkBlock):

    class Meta:
        template = 'components/blocks/button_link_block.html'


class CarrotLinkBlock(LinkBlock):

    class Meta:
        template = 'components/blocks/button_carrot_block.html'


class ListOfLinksBlock(blocks.StructBlock):
    """A collection of links that can be either button or carrot style."""

    title = blocks.CharBlock(
        required=False,
        help_text="Optional title for the list of links"
    )

    links = blocks.StreamBlock([
        ('button_link', ButtonLinkBlock(label='Button Style Link')),
        ('carrot_link', CarrotLinkBlock(label='Carrot Style Link')),
    ])

    class Meta:
        template = 'components/blocks/list_of_links_block.html'
        icon = 'list-ul'
        label = 'List of Links'
