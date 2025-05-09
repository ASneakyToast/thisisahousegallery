'''
from housegallery.core.blocks.links import ButtonLinkBlock, CarrotLinkBlock

class HomeStreamBlock(blocks.StreamBlock):
    class Meta:
        template = 'components/streamfields/generic_stream_block.html'

    button_link = ButtonLinkBlock(
        label=('Single button'),
        icon='link'
    )
    '''
