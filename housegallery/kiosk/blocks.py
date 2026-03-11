from wagtail import blocks

from housegallery.core.blocks import GalleryBlock


class KioskStreamBlock(blocks.StreamBlock):
    """StreamBlock for the kiosk display page with gallery and mailing list subscription."""

    class Meta:
        template = 'components/streamfields/generic_stream_block.html'

    gallery = GalleryBlock(
        help_text='Images for the animated kiosk gallery display'
    )
