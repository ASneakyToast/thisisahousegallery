from wagtail import blocks
from wagtail.blocks import RichTextBlock as WagtailRichTextBlock

from housegallery.core.blocks import GalleryBlock


class KioskImageSourceBlock(blocks.StreamBlock):
    """Image sources for the kiosk gallery display."""

    gallery = GalleryBlock(
        help_text='Images for the kiosk display (carousel or static)'
    )

    class Meta:
        template = 'components/streamfields/generic_stream_block.html'


class KioskHeadingBlock(blocks.StructBlock):
    """Heading text for kiosk displays."""

    text = blocks.CharBlock(required=True, max_length=255)
    size = blocks.ChoiceBlock(
        choices=[
            ('h1', 'Large (H1)'),
            ('h2', 'Medium (H2)'),
            ('h3', 'Small (H3)'),
        ],
        default='h1',
    )

    class Meta:
        template = 'components/blocks/kiosk/heading_block.html'
        icon = 'title'
        label = 'Heading'


class KioskTextBlock(blocks.StructBlock):
    """Rich text block for kiosk displays."""

    text = WagtailRichTextBlock(
        features=['bold', 'italic', 'link'],
    )

    class Meta:
        template = 'components/blocks/kiosk/text_block.html'
        icon = 'pilcrow'
        label = 'Text'


class QRCodeBlock(blocks.StructBlock):
    """QR code display block."""

    url = blocks.URLBlock(required=True, help_text="URL the QR code links to")
    size = blocks.ChoiceBlock(
        choices=[
            ('small', 'Small'),
            ('medium', 'Medium'),
            ('large', 'Large'),
        ],
        default='medium',
    )

    class Meta:
        template = 'components/blocks/kiosk/qr_code_block.html'
        icon = 'link-external'
        label = 'QR Code'


class MailingListBlock(blocks.StructBlock):
    """Mailing list signup block for kiosk displays."""

    prompt = blocks.CharBlock(
        required=False,
        max_length=255,
        default="Stay connected with our gallery",
        help_text="Text to encourage mailing list subscription",
    )
    button_text = blocks.CharBlock(
        required=False,
        max_length=50,
        default="Subscribe",
        help_text="Text for the subscribe button",
    )

    class Meta:
        template = 'components/blocks/kiosk/mailing_list_block.html'
        icon = 'mail'
        label = 'Mailing List Signup'


class KioskBodyBlock(blocks.StreamBlock):
    """Composable content blocks for kiosk body."""

    heading = KioskHeadingBlock()
    text = KioskTextBlock()
    qr_code = QRCodeBlock()
    mailing_list = MailingListBlock()
