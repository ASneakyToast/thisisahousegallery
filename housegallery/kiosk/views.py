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
            return render(request, 'pages/kiosk/kiosk_fallback.html', {
                'gallery_title': 'This is a House Gallery',
                'message': 'Kiosk page not configured. Please create a Kiosk Display Page as a child of the HomePage in the Wagtail admin, then add gallery blocks with images.'
            })

        return kiosk_page.serve(request)
    except Exception:
        return render(request, 'pages/kiosk/kiosk_fallback.html', {
            'gallery_title': 'This is a House Gallery',
            'message': 'Gallery display temporarily unavailable.'
        })
