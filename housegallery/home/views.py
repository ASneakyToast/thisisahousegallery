from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

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


@require_POST
@csrf_exempt
def mailing_list_subscribe(request):
    """
    Handle mailing list subscription from the kiosk display.
    Returns JSON response for AJAX handling.
    """
    email = request.POST.get('email', '').strip()
    
    if not email:
        return JsonResponse({
            'success': False,
            'error': 'Email address is required.'
        }, status=400)
    
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({
            'success': False,
            'error': 'Please enter a valid email address.'
        }, status=400)
    
    # TODO: Integrate with actual mailing list service (Mailchimp, ConvertKit, etc.)
    # For now, just log the subscription attempt
    
    return JsonResponse({
        'success': True,
        'message': 'Thank you for subscribing to our mailing list!'
    })