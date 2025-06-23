from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.blocks import SnippetChooserBlock

from housegallery.core.blocks.links import ButtonLinkBlock, CarrotLinkBlock, ListOfLinksBlock
from housegallery.core.blocks import SnippetGalleryBlock


class ExhibitionImageBlock(blocks.StructBlock):
    """An image block for exhibition images with optional link to artwork."""
    image = ImageChooserBlock(required=True)
    caption = blocks.CharBlock(required=False, help_text="Optional caption for the image")
    artwork = SnippetChooserBlock('artworks.Artwork', required=False, help_text="Select related artwork if applicable")
    is_installation_shot = blocks.BooleanBlock(required=False, default=False, help_text="Check if this is an installation shot (not a specific artwork)")
    
    class Meta:
        template = 'components/exhibitions/exhibition_image_block.html'
        icon = 'image'
        label = 'Exhibition Image'


class ExhibitionShowcardBlock(blocks.StructBlock):
    """Block for exhibition showcards (promotional postcards)."""
    front_image = ImageChooserBlock(required=True, help_text="Front side of the show card")
    back_image = ImageChooserBlock(required=False, help_text="Back side of the show card (optional)")
    
    class Meta:
        template = 'components/exhibitions/exhibition_showcard_block.html'
        icon = 'doc-full'
        label = 'Exhibition Showcard'


class ExhibitionGalleryBlock(blocks.StreamBlock):
    """A gallery of exhibition images."""
    image = ExhibitionImageBlock()
    showcard = ExhibitionShowcardBlock()
    
    class Meta:
        template = 'components/exhibitions/exhibition_gallery_block.html'
        icon = 'image'
        label = 'Exhibition Gallery'




class ExhibitionStreamBlock(blocks.StreamBlock):
    """Stream block specifically for exhibition pages."""
    gallery = ExhibitionGalleryBlock(label='Image Gallery')
    snippet_gallery = SnippetGalleryBlock(label='Gallery (Snippet)')
    rich_text = blocks.RichTextBlock(label='Rich Text')
    button_link = ButtonLinkBlock(label='Button Link')
    list_of_links = ListOfLinksBlock(label='List of Links')
    
    class Meta:
        template = 'components/streamfields/generic_stream_block.html'