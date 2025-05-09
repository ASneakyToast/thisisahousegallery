from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.models import Orderable
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.images.models import Image
from wagtail.documents.models import Document
from wagtail.snippets.models import register_snippet
from wagtail.fields import StreamField
from wagtail.blocks import StructBlock, CharBlock, RichTextBlock, ListBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.documents.blocks import DocumentChooserBlock


class ArtworkTextBlock(StructBlock):
    text = RichTextBlock(
        required=True,
        max_length=255
    )

    class Meta:
        template = 'blocks/artwork_text_block.html'
        icon = 'doc-full'


class ArtworkImageBlock(StructBlock):
    image = ImageChooserBlock(
        required=True
    )
    caption = CharBlock(
        required=False,
        max_length=255
    )

    class Meta:
        template = 'blocks/artwork_image_block.html'
        icon = 'image'


class ArtworkDocumentBlock(StructBlock):
    document = DocumentChooserBlock(
        required=True
    )
    title = CharBlock(
        required=False,
        max_length=255
    )
    description = RichTextBlock(
        required=False,
        max_length=255
    )

    class Meta:
        template = 'blocks/artwork_document_block.html'
        icon = 'doc-full'


@register_snippet
class Artwork(ClusterableModel):
    title = models.CharField(
        blank=False,
        max_length=255
    )
    artist = models.ForeignKey(
        'artists.Artist',
        null=True,
        blank=True,
        on_delete=models.PROTECT,  # Using PROTECT to prevent deletion of an artist with artworks
        related_name='artworks'
    )
    description = models.TextField(
        blank=True,
        max_length=255
    )
    materials = models.TextField(
        blank=True,
        max_length=255
    )
    size = models.CharField(
        blank=True,
        max_length=255,
        help_text="Height x Width x Depth"
    )
    date = models.DateTimeField(
        blank=True,
        null=True,
    )
    artifacts = StreamField([
        ('image', ArtworkImageBlock()),
        ('document', ArtworkDocumentBlock()),
        ('text', ArtworkTextBlock()),
    ], blank=True)

    panels = [
        FieldPanel('title'),
        FieldPanel('artist'),
        FieldPanel('date'),
        FieldPanel('description'),
        FieldPanel('artifacts'),
    ]

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Artwork"
        verbose_name_plural = "Artworks"
