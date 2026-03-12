from wagtail import blocks
from wagtail.blocks import RichTextBlock as WagtailRichTextBlock
from wagtail.snippets.blocks import SnippetChooserBlock

from housegallery.core.blocks.images import AllImagesBlock
from housegallery.core.blocks.images import SingleImageBlock
from housegallery.core.blocks.images import TaggedSetBlock

IMAGE_CATEGORY_CHOICES = [
    ("exhibition", "Installation Photos"),
    ("opening", "Opening Reception"),
    ("showcards", "Showcards"),
    ("in_progress", "In Progress Shots"),
    ("artwork", "Artwork Images"),
]


class KioskImageSourceBlock(blocks.StreamBlock):
    """Image sources for kiosk display — maps directly to gallery item types."""

    single_image = SingleImageBlock()
    tagged_set = TaggedSetBlock()
    all_images = AllImagesBlock()

    class Meta:
        template = "components/streamfields/generic_stream_block.html"


class KioskArtworkBlock(blocks.StructBlock):
    """Feature an artwork with its images and metadata in the kiosk carousel."""

    artwork = SnippetChooserBlock("artworks.Artwork")

    class Meta:
        template = "components/blocks/kiosk/artwork_block.html"
        icon = "image"
        label = "Artwork"


class KioskExhibitionBlock(blocks.StructBlock):
    """Feature an exhibition's images in the kiosk carousel."""

    exhibition = blocks.PageChooserBlock(page_type="exhibitions.ExhibitionPage")
    max_images = blocks.IntegerBlock(
        required=False,
        min_value=1,
        help_text="Limit the number of images shown (leave blank for all)",
    )
    image_categories = blocks.MultipleChoiceBlock(
        choices=IMAGE_CATEGORY_CHOICES,
        required=False,
        help_text="Which image categories to include (leave blank for all)",
    )

    class Meta:
        template = "components/blocks/kiosk/exhibition_block.html"
        icon = "doc-full"
        label = "Exhibition"


class KioskArtistBlock(blocks.StructBlock):
    """Feature an artist's artwork images in the kiosk carousel."""

    artist = SnippetChooserBlock("artists.Artist")

    class Meta:
        template = "components/blocks/kiosk/artist_block.html"
        icon = "user"
        label = "Artist"


class KioskFeaturedItemsBlock(blocks.StreamBlock):
    """Featured items for kiosk display — artworks, exhibitions, artists, and images."""

    artwork = KioskArtworkBlock()
    exhibition = KioskExhibitionBlock()
    artist = KioskArtistBlock()
    single_image = SingleImageBlock()
    tagged_set = TaggedSetBlock()
    all_images = AllImagesBlock()

    class Meta:
        template = "components/streamfields/generic_stream_block.html"


class KioskHeadingBlock(blocks.StructBlock):
    """Heading text for kiosk displays."""

    text = blocks.CharBlock(required=True, max_length=255)
    size = blocks.ChoiceBlock(
        choices=[
            ("h1", "Large (H1)"),
            ("h2", "Medium (H2)"),
            ("h3", "Small (H3)"),
        ],
        default="h1",
    )

    class Meta:
        template = "components/blocks/kiosk/heading_block.html"
        icon = "title"
        label = "Heading"


class KioskTextBlock(blocks.StructBlock):
    """Rich text block for kiosk displays."""

    text = WagtailRichTextBlock(
        features=["bold", "italic", "link"],
    )

    class Meta:
        template = "components/blocks/kiosk/text_block.html"
        icon = "pilcrow"
        label = "Text"


class QRCodeBlock(blocks.StructBlock):
    """QR code display block."""

    url = blocks.URLBlock(required=True, help_text="URL the QR code links to")
    size = blocks.ChoiceBlock(
        choices=[
            ("small", "Small"),
            ("medium", "Medium"),
            ("large", "Large"),
        ],
        default="medium",
    )

    class Meta:
        template = "components/blocks/kiosk/qr_code_block.html"
        icon = "link-external"
        label = "QR Code"


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
        template = "components/blocks/kiosk/mailing_list_block.html"
        icon = "mail"
        label = "Mailing List Signup"


class KioskBodyBlock(blocks.StreamBlock):
    """Composable content blocks for kiosk body."""

    heading = KioskHeadingBlock()
    text = KioskTextBlock()
    qr_code = QRCodeBlock()
    mailing_list = MailingListBlock()
