from django.db import models
from django.utils.html import strip_tags, format_html
from django.contrib.contenttypes.fields import GenericRelation

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

from wagtail.models import Orderable, DraftStateMixin, RevisionMixin
from wagtail.admin.panels import FieldPanel, InlinePanel, MultipleChooserPanel, MultiFieldPanel, PublishingPanel
from wagtail.images.models import Image
from wagtail.documents.models import Document
from wagtail.fields import StreamField, RichTextField
from wagtail.blocks import StructBlock, CharBlock, RichTextBlock, ListBlock, ChoiceBlock, BooleanBlock, StreamBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images import get_image_model_string
from wagtail.search import index

from housegallery.exhibitions.views import ExhibitionImageChooserWidget
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
        indexes = [
            models.Index(fields=['artwork', 'artist'], name='artwork_artist_idx'),
        ]


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
        ordering = ["sort_order"]


class Artwork(DraftStateMixin, RevisionMixin, ClusterableModel):
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
    
    # Required for RevisionMixin
    _revisions = GenericRelation("wagtailcore.Revision", related_query_name="artwork")

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
        PublishingPanel(),
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
    
    @property
    def materials_list(self):
        """Return materials as comma-separated list for admin display"""
        return ", ".join([tag.name for tag in self.materials.all()]) or "-"

    @property  
    def description_preview(self):
        """Return truncated description for admin display"""
        if self.description:
            return (self.description[:75] + '...') if len(self.description) > 75 else self.description
        return "-"
    
    def date_year(self):
        """Return just the year from the date field for admin display"""
        if self.date:
            return self.date.year
        return "-"
    date_year.short_description = "Date"
    date_year.admin_order_field = "date"
    
    def admin_thumb(self):
        """Return thumbnail HTML for admin list display"""
        first_image = self.artwork_images.first()
        if first_image and first_image.image:
            try:
                rendition = first_image.image.get_rendition('fill-60x60')
                return format_html(
                    '<img src="{}" width="60" height="60" alt="{}" />',
                    rendition.url,
                    f"Thumbnail for {self}"
                )
            except Exception:
                return "-"
        return "-"
    admin_thumb.short_description = "Thumbnail"
    
    def title_sortable(self):
        """Return artwork title with explicit sorting"""
        return strip_tags(self.title) if self.title else "Untitled"
    title_sortable.short_description = "Title"
    title_sortable.admin_order_field = "title"
    
    def date_published(self):
        """Return the first published date for admin display"""
        if self.first_published_at:
            return self.first_published_at.strftime('%Y-%m-%d')
        return "-"
    date_published.short_description = "Date Added"
    date_published.admin_order_field = "first_published_at"
    
    search_fields = [
        index.SearchField('title'),
        index.SearchField('description'),
        index.SearchField('artist_names'),
        index.FilterField('date'),
        index.FilterField('id'),
        index.RelatedFields('artists', [
            index.SearchField('name'),
        ]),
        index.RelatedFields('materials', [
            index.SearchField('name'),
        ]),
    ]

    class Meta:
        verbose_name = "Artwork"
        verbose_name_plural = "Artworks"
        indexes = [
            models.Index(fields=['-date', 'title'], name='artwork_date_title_idx'),
        ]
