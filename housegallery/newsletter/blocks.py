from wagtail.blocks import (
    CharBlock,
    ChoiceBlock,
    RichTextBlock,
    StaticBlock,
    StreamBlock,
    StructBlock,
    URLBlock,
)
from wagtail.images.blocks import ImageChooserBlock


class EmailHeadingBlock(StructBlock):
    text = CharBlock(required=True)
    level = ChoiceBlock(
        choices=[("h1", "Heading 1"), ("h2", "Heading 2")],
        default="h2",
    )

    class Meta:
        template = "newsletter/blocks/email_heading_block.html"
        icon = "title"
        label = "Heading"


class EmailTextBlock(RichTextBlock):
    def __init__(self, **kwargs):
        kwargs.setdefault("features", ["bold", "italic", "link"])
        super().__init__(**kwargs)

    class Meta:
        template = "newsletter/blocks/email_text_block.html"
        icon = "pilcrow"
        label = "Text"


class EmailImageSectionBlock(StructBlock):
    heading = CharBlock(required=False, help_text="Optional section heading")
    image = ImageChooserBlock(required=True)
    image_link = URLBlock(required=False, help_text="URL the image links to")
    description = RichTextBlock(
        features=["bold", "italic", "link"],
        required=False,
        help_text="Text below the image",
    )
    link_url = URLBlock(required=False, help_text="CTA link URL")
    link_text = CharBlock(required=False, help_text="CTA link text")

    class Meta:
        template = "newsletter/blocks/email_image_section_block.html"
        icon = "image"
        label = "Image Section"


class EmailDividerBlock(StaticBlock):
    class Meta:
        template = "newsletter/blocks/email_divider_block.html"
        icon = "horizontalrule"
        label = "Divider"
        admin_text = "Horizontal divider"


class NewsletterStreamBlock(StreamBlock):
    heading = EmailHeadingBlock()
    text = EmailTextBlock()
    image_section = EmailImageSectionBlock()
    divider = EmailDividerBlock()
