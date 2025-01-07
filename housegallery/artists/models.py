from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.images.models import Image
from wagtail.images import get_image_model_string
from wagtail.snippets.models import register_snippet
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


@register_snippet
class Artist(ClusterableModel):
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
    birth_year = models.IntegerField(null=True, blank=True)
    social_media_links = StreamField(
        [('social_link', SocialMediaLinkBlock())],
        blank=True,
        help_text="Add social media profiles for this artist"
    )

    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('bio'),
            FieldPanel('profile_image'),
            FieldPanel('website'),
            FieldPanel('birth_year'),
        ], heading="Artist Details"),
        FieldPanel('social_media_links', heading="Social Media Profiles"),
    ]
      
    search_fields = [
        index.SearchField('name'),
        index.SearchField('bio'),
        index.FilterField('birth_year'),
	]
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Artist"
        verbose_name_plural = "Artists"
        ordering = ['name']
