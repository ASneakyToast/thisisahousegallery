import logging
import uuid

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Newsletter, Subscriber

logger = logging.getLogger(__name__)


def _get_client_ip(request):
    """Extract client IP from request, respecting X-Forwarded-For."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@require_POST
def subscribe(request):
    """Handle newsletter subscription. Returns JSON for AJAX forms."""
    # Rate limit: 5 requests per minute per IP
    ip = _get_client_ip(request)
    cache_key = f"newsletter_subscribe_{ip}"
    request_count = cache.get(cache_key, 0)
    if request_count >= 5:
        return JsonResponse(
            {"success": False, "error": "Too many requests. Please try again later."},
            status=429,
        )
    cache.set(cache_key, request_count + 1, 60)

    email = request.POST.get("email", "").strip().lower()

    if not email:
        return JsonResponse(
            {"success": False, "error": "Email address is required."}, status=400
        )

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse(
            {"success": False, "error": "Please enter a valid email address."},
            status=400,
        )

    subscriber, created = Subscriber.objects.get_or_create(
        email=email,
        defaults={},
    )

    if not created and subscriber.is_active:
        return JsonResponse(
            {"success": True, "message": "You're already subscribed!"}
        )

    # If they previously unsubscribed, re-activate the flow
    if not created and subscriber.unsubscribed_at:
        subscriber.unsubscribed_at = None
        subscriber.confirmed = False
        subscriber.confirmation_token = uuid.uuid4()
        subscriber.save(
            update_fields=["unsubscribed_at", "confirmed", "confirmation_token"]
        )

    # Send confirmation email
    try:
        _send_confirmation_email(request, subscriber)
    except Exception:
        logger.exception("Failed to send confirmation email")
        return JsonResponse(
            {"success": False, "error": "Could not send confirmation email. Please try again later."},
            status=500,
        )

    return JsonResponse(
        {
            "success": True,
            "message": "Please check your email to confirm your subscription.",
        }
    )


def confirm(request, token):
    """Confirm a subscription via the emailed token."""
    subscriber = get_object_or_404(Subscriber, confirmation_token=token)

    already_confirmed = subscriber.confirmed
    if not already_confirmed:
        subscriber.confirm()

    return render(
        request,
        "newsletter/confirm.html",
        {"subscriber": subscriber, "already_confirmed": already_confirmed},
    )


def unsubscribe(request, token):
    """Unsubscribe via the token included in every newsletter.

    GET shows a confirmation page; POST performs the unsubscribe.
    """
    subscriber = get_object_or_404(Subscriber, unsubscribe_token=token)

    already_unsubscribed = subscriber.unsubscribed_at is not None

    if request.method == "POST" and not already_unsubscribed:
        subscriber.unsubscribe()
        return render(
            request,
            "newsletter/unsubscribe.html",
            {"subscriber": subscriber, "unsubscribed": True, "already_unsubscribed": False},
        )

    return render(
        request,
        "newsletter/unsubscribe.html",
        {"subscriber": subscriber, "unsubscribed": False, "already_unsubscribed": already_unsubscribed},
    )


def signup_page(request):
    """Dedicated newsletter signup page."""
    return render(request, "newsletter/signup_page.html")


def unsubscribe_request_page(request):
    """Dedicated page for entering email to unsubscribe."""
    return render(request, "newsletter/unsubscribe_request_page.html")


@require_POST
def unsubscribe_request(request):
    """Handle unsubscribe-by-email requests. Returns JSON for AJAX forms."""
    # Rate limit: 5 requests per minute per IP
    ip = _get_client_ip(request)
    cache_key = f"newsletter_unsubscribe_{ip}"
    request_count = cache.get(cache_key, 0)
    if request_count >= 5:
        return JsonResponse(
            {"success": False, "error": "Too many requests. Please try again later."},
            status=429,
        )
    cache.set(cache_key, request_count + 1, 60)

    email = request.POST.get("email", "").strip().lower()

    if not email:
        return JsonResponse(
            {"success": False, "error": "Email address is required."}, status=400
        )

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse(
            {"success": False, "error": "Please enter a valid email address."},
            status=400,
        )

    # Look up subscriber and send confirmation if active
    try:
        subscriber = Subscriber.objects.get(email=email)
        if subscriber.is_active:
            _send_unsubscribe_email(request, subscriber)
    except Subscriber.DoesNotExist:
        pass
    except Exception:
        logger.exception("Failed to send unsubscribe confirmation email")

    # Always return the same message for privacy
    return JsonResponse(
        {
            "success": True,
            "message": "If this email is subscribed, you'll receive an email with an unsubscribe link.",
        }
    )


@staff_member_required
def preview(request, slug):
    """Staff-only preview of a newsletter edition."""
    newsletter = get_object_or_404(Newsletter, slug=slug)

    context = {
        "newsletter": newsletter,
        "subscriber": None,
        "unsubscribe_url": "#",
        "preview_mode": True,
    }

    return render(request, newsletter.template_path, context)


def _send_unsubscribe_email(request, subscriber):
    """Send an email with the unsubscribe link for confirmation."""
    unsubscribe_path = reverse(
        "newsletter:unsubscribe", args=[subscriber.unsubscribe_token]
    )
    unsubscribe_url = request.build_absolute_uri(unsubscribe_path)

    subject = "Unsubscribe from This is a House Gallery"
    html_message = render_to_string(
        "newsletter/emails/confirm_unsubscribe.html",
        {"unsubscribe_url": unsubscribe_url, "email": subscriber.email},
    )
    text_message = render_to_string(
        "newsletter/emails/confirm_unsubscribe.txt",
        {"unsubscribe_url": unsubscribe_url, "email": subscriber.email},
    )

    from_email = getattr(
        settings, "DEFAULT_FROM_EMAIL", "noreply@thisisahousegallery.com"
    )

    send_mail(
        subject=subject,
        message=text_message,
        from_email=from_email,
        recipient_list=[subscriber.email],
        html_message=html_message,
        fail_silently=False,
    )


def _send_confirmation_email(request, subscriber):
    """Send the double opt-in confirmation email."""
    confirm_path = reverse("newsletter:confirm", args=[subscriber.confirmation_token])
    confirm_url = request.build_absolute_uri(confirm_path)

    subject = "Confirm your subscription to This is a House Gallery"
    html_message = render_to_string(
        "newsletter/emails/confirm_subscription.html",
        {"confirm_url": confirm_url, "email": subscriber.email},
    )
    text_message = render_to_string(
        "newsletter/emails/confirm_subscription.txt",
        {"confirm_url": confirm_url, "email": subscriber.email},
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@thisisahousegallery.com")

    send_mail(
        subject=subject,
        message=text_message,
        from_email=from_email,
        recipient_list=[subscriber.email],
        html_message=html_message,
        fail_silently=False,
    )
