from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

from wagtail.models import Orderable
from wagtail.admin.panels import FieldPanel, InlinePanel, MultipleChooserPanel, MultiFieldPanel
from wagtail.images.models import Image
from wagtail.documents.models import Document
from wagtail.snippets.models import register_snippet
from wagtail.fields import StreamField
from wagtail.blocks import StructBlock, CharBlock, RichTextBlock, ListBlock, ChoiceBlock, BooleanBlock, StreamBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images import get_image_model_string

from housegallery.exhibitions.widgets import ExhibitionImageChooserPanel



class ArtworkTag(TaggedItemBase):
    content_object = ParentalKey('Artwork', related_name='tagged_items', on_delete=models.CASCADE)


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




class ArtworkImage(Orderable):
    """Through model for artwork gallery images with MultipleChooserPanel"""
    artwork = ParentalKey(
        'Artwork',
        on_delete=models.CASCADE,
        related_name='artwork_images'
    )
    image = models.ForeignKey(
        get_image_model_string(),
        on_delete=models.CASCADE,
        related_name='+'
    )
    caption = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional caption for this image"
    )

    panels = [
        ExhibitionImageChooserPanel('image'),
        FieldPanel('caption'),
    ]

    class Meta:
        verbose_name = "Artwork Image"
        verbose_name_plural = "Artwork Images"


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
    materials = ClusterTaggableManager(through=ArtworkTag, blank=True)
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
    cover_image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Main cover image for this artwork"
    )

    panels = [
        FieldPanel('title'),
        FieldPanel('artist'),
        FieldPanel('date'),
        FieldPanel('size'),
        FieldPanel('materials'),
        FieldPanel('description'),
        FieldPanel('cover_image'),
        MultiFieldPanel([
            MultipleChooserPanel(
                'artwork_images',
                label="Images",
                chooser_field_name="image"
            ),
        ], heading="Gallery Images"),
        FieldPanel('artifacts'),
    ]

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Artwork"
        verbose_name_plural = "Artworks"
