from django.utils.html import format_html
from django.urls import reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from .views import exhibition_image_chooser_viewset
from .models import EventPage, SchedulePage

@hooks.register('register_admin_viewset')
def register_exhibition_image_chooser_viewset():
    return exhibition_image_chooser_viewset

@hooks.register('insert_global_admin_css')
def admin_chooser_css():
    """Add CSS for image chooser preview enhancements."""
    return format_html('<link rel="stylesheet" href="{}">', '/static/css/components/admin-chooser.css')


@hooks.register('register_admin_menu_item')
def register_events_menu_item():
    """Add Events menu item that goes to Schedule page in page explorer"""
    try:
        # Try to find the schedule page to link to
        schedule_page = SchedulePage.objects.first()
        if schedule_page:
            # Create URL to schedule page in page explorer
            url = reverse('wagtailadmin_explore', args=[schedule_page.id])
            return MenuItem(
                'Events',
                url,
                icon_name='date',
                order=200
            )
    except:
        pass
    return None