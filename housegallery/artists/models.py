from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.images.models import Image
from wagtail.images import get_image_model_string
from wagtail.snippets.models import register_snippet
from wagtail.search import index


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
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('bio'),
            FieldPanel('profile_image'),
            FieldPanel('website'),
            FieldPanel('birth_year'),
        ], heading="Artist Details"),
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
