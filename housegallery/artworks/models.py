from django.db import models
from django.utils.html import strip_tags

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

from wagtail.models import Orderable
from wagtail.admin.panels import FieldPanel, InlinePanel, MultipleChooserPanel, MultiFieldPanel
from wagtail.images.models import Image
from wagtail.documents.models import Document
from wagtail.snippets.models import register_snippet
from wagtail.fields import StreamField, RichTextField
from wagtail.blocks import StructBlock, CharBlock, RichTextBlock, ListBlock, ChoiceBlock, BooleanBlock, StreamBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images import get_image_model_string

from housegallery.exhibitions.widgets import ExhibitionImageChooserPanel, ExhibitionImageChooserWidget
from housegallery.artists.widgets import ArtistChooserPanel



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




class ArtworkArtist(Orderable):
    """Through model for artwork-artist many-to-many relationship"""
    artwork = ParentalKey(
        'Artwork',
        on_delete=models.CASCADE,
        related_name='artwork_artists'
    )
    artist = models.ForeignKey(
        'artists.Artist',
        on_delete=models.CASCADE,
        related_name='+'
    )

    panels = [
        ArtistChooserPanel('artist'),
    ]

    class Meta:
        verbose_name = "Artwork Artist"
        verbose_name_plural = "Artwork Artists"
        unique_together = ['artwork', 'artist']  # Prevent duplicate artist assignments


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
        FieldPanel('image', widget=ExhibitionImageChooserWidget()),
        FieldPanel('caption'),
    ]

    class Meta:
        verbose_name = "Artwork Image"
        verbose_name_plural = "Artwork Images"


@register_snippet
class Artwork(ClusterableModel):
    title = RichTextField(
        blank=True
    )
    # Many-to-many field for multiple artists
    artists = ParentalManyToManyField(
        'artists.Artist',
        through='ArtworkArtist',
        blank=True,
        related_name='artwork_list'
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

    panels = [
        FieldPanel('title'),
        # Artist management panel
        InlinePanel('artwork_artists', label="Artists"),
        FieldPanel('date'),
        FieldPanel('size'),
        FieldPanel('materials'),
        FieldPanel('description'),
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
        if self.title:
            return strip_tags(self.title)
        
        # Format for untitled artworks: _untitled_ (artist name #id)
        artist_name = self.artist_names if self.artist_names else "Unknown Artist"
        return f"_untitled_ ({artist_name} #{self.id})"
    
    @property
    def artist_names(self):
        """Return comma-separated list of artist names"""
        return ", ".join([artist.name for artist in self.artists.all()])
    
    @property
    def first_artist(self):
        """Return first artist for backward compatibility"""
        return self.artists.first()
    
    def get_artists(self):
        """Return all artists for this artwork"""
        return self.artists.all()

    class Meta:
        verbose_name = "Artwork"
        verbose_name_plural = "Artworks"
