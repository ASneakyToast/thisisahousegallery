import secrets
from django.db import models
from django.db.models import F
from django.utils import timezone
from housegallery.artists.models import Artist


class APIKey(models.Model):
    """API key model for multi-tenant authentication"""
    
    key = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        blank=True,
        help_text="The API key. Generated automatically if not provided."
    )
    name = models.CharField(
        max_length=100,
        help_text="Human-readable identifier for this API key"
    )
    artist = models.ForeignKey(
        Artist, 
        on_delete=models.CASCADE,
        related_name='api_keys',
        help_text="The artist this API key provides access to"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this API key is currently active"
    )
    rate_limit = models.PositiveIntegerField(
        default=1000,
        help_text="Maximum requests per hour allowed with this key"
    )
    allowed_ips = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of allowed IP addresses. Empty list allows all IPs."
    )
    
    created = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ['-created']
    
    def __str__(self):
        return f"{self.name} ({self.artist.name})"
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_key():
        """Generate cryptographically secure API key"""
        return secrets.token_urlsafe(48)
    
    def update_usage(self):
        """Update usage statistics for this key"""
        self.last_used = timezone.now()
        self.usage_count = F('usage_count') + 1
        self.save(update_fields=['last_used', 'usage_count'])