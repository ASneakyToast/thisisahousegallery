from django.shortcuts import render

from .models import KioskPage


def find_kiosk_by_slug(slug):
    """Look up a live kiosk page by slug."""
    try:
        return KioskPage.objects.live().get(slug=slug)
    except KioskPage.DoesNotExist:
        return None


def find_all_live_kiosks():
    """Return all live kiosk pages."""
    return list(KioskPage.objects.live())


def kiosk_display(request, kiosk_slug):
    """Serve a specific kiosk display by its page slug at /display/<slug>/."""
    try:
        kiosk_page = find_kiosk_by_slug(kiosk_slug)
        if kiosk_page:
            return kiosk_page.serve(request)
        return render(request, 'pages/kiosk/kiosk_fallback.html', {
            'gallery_title': 'This is a House Gallery',
            'message': f'No kiosk display found for "{kiosk_slug}". '
                       'Please check the URL or configure a kiosk in the admin.',
        })
    except Exception:
        return render(request, 'pages/kiosk/kiosk_fallback.html', {
            'gallery_title': 'This is a House Gallery',
            'message': 'Gallery display temporarily unavailable.',
        })


def kiosk_list_or_default(request):
    """
    If exactly one live kiosk exists, serve it directly.
    Otherwise show the fallback listing available kiosks.
    """
    try:
        live_kiosks = find_all_live_kiosks()
        count = len(live_kiosks)

        if count == 1:
            return live_kiosks[0].serve(request)

        if count == 0:
            return render(request, 'pages/kiosk/kiosk_fallback.html', {
                'gallery_title': 'This is a House Gallery',
                'message': 'Kiosk page not configured. Please create a Kiosk '
                           'Display Page as a child of the HomePage in the '
                           'Wagtail admin, then add gallery blocks with images.',
            })

        # Multiple kiosks — show listing
        return render(request, 'pages/kiosk/kiosk_fallback.html', {
            'gallery_title': 'This is a House Gallery',
            'message': 'Multiple kiosk displays are available.',
            'kiosks': live_kiosks,
        })
    except Exception:
        return render(request, 'pages/kiosk/kiosk_fallback.html', {
            'gallery_title': 'This is a House Gallery',
            'message': 'Gallery display temporarily unavailable.',
        })
