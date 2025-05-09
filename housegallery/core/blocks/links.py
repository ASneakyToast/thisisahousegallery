from wagtail import blocks

from housegallery.core.utils import LinkBlock


class ButtonLinkBlock(LinkBlock):
    
    class Meta:
        template = 'components/blocks/button_link_block.html'


class CarrotLinkBlock(LinkBlock):

    class Meta:
        template = 'components/blocks/button_carrot_block.html'
