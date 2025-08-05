from django.db import models
from django.utils.html import format_html
from django.contrib.contenttypes.fields import GenericRelation

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.models import DraftStateMixin, RevisionMixin
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, PublishingPanel
from wagtail.images.models import Image
from wagtail.images import get_image_model_string
from wagtail.search import index
from wagtail.fields import StreamField
from wagtail.blocks import StructBlock, CharBlock, URLBlock, ChoiceBlock


class SocialMediaLinkBlock(StructBlock):
    """
    A block for social media links.
    """
    platform = ChoiceBlock(
        choices=[
            ('instagram', 'Instagram'),
            ('facebook', 'Facebook'),
            ('twitter', 'Twitter'),
            ('linkedin', 'LinkedIn'),
            ('youtube', 'YouTube'),
            ('tiktok', 'TikTok'),
            ('pinterest', 'Pinterest'),
            ('vimeo', 'Vimeo'),
            ('other', 'Other Platform'),
        ],
        required=True,
        help_text="Select the social media platform"
    )
    platform_name = CharBlock(
        required=False,
        max_length=50,
        help_text="If 'Other Platform' is selected, specify the platform name here"
    )
    url = URLBlock(
        required=True,
        help_text="Full URL to the social media profile"
    )
    handle = CharBlock(
        required=False,
        max_length=100,
        help_text="Username/handle (without the @ symbol)"
    )

    class Meta:
        icon = 'link'
        template = 'blocks/social_media_link_block.html'


class Artist(DraftStateMixin, RevisionMixin, ClusterableModel):
    """
    A snippet model representing an artist.
    """
    name = models.CharField(
        max_length=255
    )
    bio = models.TextField(
        blank=True
    )
    profile_image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    website = models.URLField(
        blank=True
    )
    email = models.EmailField(
        blank=True,
        help_text="Artist's contact email address"
    )
    birth_year = models.IntegerField(null=True, blank=True)
    social_media_links = StreamField(
        [('social_link', SocialMediaLinkBlock())],
        blank=True,
        help_text="Add social media profiles for this artist"
    )
    
    # Required for RevisionMixin
    _revisions = GenericRelation("wagtailcore.Revision", related_query_name="artist")

    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('bio'),
            FieldPanel('profile_image'),
            FieldPanel('website'),
            FieldPanel('email'),
            FieldPanel('birth_year'),
        ], heading="Artist Details"),
        FieldPanel('social_media_links', heading="Social Media Profiles"),
        PublishingPanel(),
    ]
      
    search_fields = [
        index.SearchField('name'),
        index.SearchField('bio'),
        index.FilterField('birth_year'),
	]
    
    def __str__(self):
        return self.name
    
    def admin_thumb(self):
        """Return thumbnail HTML for admin list display"""
        if self.profile_image:
            try:
                rendition = self.profile_image.get_rendition('fill-60x60')
                return format_html(
                    '<img src="{}" width="60" height="60" alt="{}" />',
                    rendition.url,
                    f"Profile photo of {self.name}"
                )
            except Exception:
                return "-"
        return "-"
    admin_thumb.short_description = "Photo"
    
    def bio_preview(self):
        """Return truncated bio for admin display"""
        if self.bio:
            return (self.bio[:75] + '...') if len(self.bio) > 75 else self.bio
        return "-"
    bio_preview.short_description = "Bio"
    
    def artwork_count(self):
        """Return count of artworks by this artist"""
        # Use annotated count if available, otherwise fall back to query
        if hasattr(self, 'artwork_count_annotated'):
            return self.artwork_count_annotated
        return self.artwork_list.count()
    artwork_count.short_description = "Artworks"
    artwork_count.admin_order_field = "artwork_count_annotated"
    
    def name_sortable(self):
        """Return artist name with explicit sorting"""
        return self.name
    name_sortable.short_description = "Name"
    name_sortable.admin_order_field = "name"
    
    def date_published(self):
        """Return the first published date for admin display"""
        if self.first_published_at:
            return self.first_published_at.strftime('%Y-%m-%d')
        return "-"
    date_published.short_description = "Date Added"
    date_published.admin_order_field = "first_published_at"
    
    class Meta:
        verbose_name = "Artist"
        verbose_name_plural = "Artists"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'], name='artist_name_idx'),
            models.Index(fields=['birth_year'], name='artist_birth_year_idx'),
        ]
