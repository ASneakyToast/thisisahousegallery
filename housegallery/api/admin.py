from django.contrib import admin
from django.utils.html import format_html
from housegallery.api.models import APIKey


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'artist', 'is_active', 'rate_limit', 'created', 'last_used', 'usage_count']
    list_filter = ['is_active', 'created', 'last_used', 'artist']
    search_fields = ['name', 'artist__name', 'key']
    readonly_fields = ['key', 'created', 'last_used', 'usage_count', 'display_key']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'artist', 'is_active')
        }),
        ('API Key', {
            'fields': ('display_key', 'key'),
            'description': 'The API key is generated automatically and cannot be changed.'
        }),
        ('Rate Limiting & Security', {
            'fields': ('rate_limit', 'allowed_ips'),
            'description': 'Leave allowed_ips empty to allow all IP addresses.'
        }),
        ('Usage Statistics', {
            'fields': ('created', 'last_used', 'usage_count'),
            'classes': ('collapse',)
        })
    )
    
    def display_key(self, obj):
        """Display the API key with a copy button"""
        if obj.key:
            return format_html(
                '<div style="font-family: monospace; background-color: #f5f5f5; padding: 8px; '
                'border-radius: 4px; display: inline-block;">{}</div>'
                '<button type="button" onclick="navigator.clipboard.writeText(\'{}\')" '
                'style="margin-left: 10px; padding: 5px 10px; cursor: pointer;">'
                'Copy to Clipboard</button>',
                obj.key, obj.key
            )
        return "Key will be generated on save"
    display_key.short_description = "API Key (click to copy)"
    
    def get_readonly_fields(self, request, obj=None):
        """Make key field readonly after creation"""
        if obj:  # Editing existing object
            return self.readonly_fields
        else:  # Creating new object
            return ['created', 'last_used', 'usage_count', 'display_key']