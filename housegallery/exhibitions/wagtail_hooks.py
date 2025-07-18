from django.utils.html import format_html
from wagtail import hooks
from .views import exhibition_image_chooser_viewset

@hooks.register('register_admin_viewset')
def register_exhibition_image_chooser_viewset():
    return exhibition_image_chooser_viewset

@hooks.register('insert_global_admin_css')
def admin_chooser_css():
    """Add CSS for image chooser preview enhancements."""
    return format_html('<link rel="stylesheet" href="{}">', '/static/css/components/admin-chooser.css')



