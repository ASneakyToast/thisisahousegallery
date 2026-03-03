from django.shortcuts import render

from .models import KioskPage


def kiosk_display(request):
    """
    Custom view for the kiosk display page accessible at /display.
    Renders the first available KioskPage.
    """
    try:
        kiosk_page = KioskPage.objects.live().first()
        if not kiosk_page:
            # If no kiosk page exists, return a simple message
            return render(request, 'pages/kiosk_fallback.html', {
                'gallery_title': 'This is a House Gallery',
                'message': 'Kiosk page not configured. Please create a Kiosk Display Page as a child of the HomePage in the Wagtail admin, then add gallery blocks with images.'
            })
        
        # Use the page's serve method to get proper context
        return kiosk_page.serve(request)
    except Exception:
        # Fallback if something goes wrong
        return render(request, 'pages/kiosk_fallback.html', {
            'gallery_title': 'This is a House Gallery',
            'message': 'Gallery display temporarily unavailable.'
        })


