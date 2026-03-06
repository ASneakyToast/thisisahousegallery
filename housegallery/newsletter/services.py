import time

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Newsletter, Subscriber
from .utils import add_utm_params, get_base_url

UNSUBSCRIBE_URL_PLACEHOLDER = "__UNSUBSCRIBE_URL__"


def send_newsletter_edition(
    newsletter,
    test_email=None,
    dry_run=False,
    batch_size=50,
    batch_delay=2.0,
    force=False,
    include_bounced=False,
    log_callback=None,
):
    """Send a newsletter edition to subscribers.

    Returns {"sent": int, "errors": int, "error_details": [...]}
    Raises ValueError for validation failures.
    """
    if newsletter.status == Newsletter.Status.SENT and not force:
        raise ValueError(
            f"Newsletter '{newsletter.slug}' was already sent on {newsletter.sent_at}. "
            "Use force=True to send again."
        )

    def log(msg):
        if log_callback:
            log_callback(msg)

    from_email = getattr(
        settings, "DEFAULT_FROM_EMAIL", "noreply@thisisahousegallery.com"
    )
    subject = newsletter.effective_subject

    # Determine recipients
    if test_email:
        recipients = [{"email": test_email, "unsubscribe_token": "test-token"}]
        log(f"TEST MODE: sending to {test_email}")
    else:
        subscribers = Subscriber.objects.filter(
            confirmed=True, unsubscribed_at__isnull=True
        )
        if not include_bounced:
            subscribers = subscribers.filter(bounce_count__lt=3)
        recipients = list(subscribers.values("email", "unsubscribe_token"))
        log(f"Sending to {len(recipients)} subscribers")

    if not recipients:
        return {"sent": 0, "errors": 0, "error_details": [], "no_recipients": True}

    if dry_run:
        return {
            "sent": 0,
            "errors": 0,
            "error_details": [],
            "dry_run": True,
            "would_send_to": [r["email"] for r in recipients],
        }

    # Pre-render template once with placeholder unsubscribe URL
    base_url = get_base_url()
    context = {
        "newsletter": newsletter,
        "unsubscribe_url": UNSUBSCRIBE_URL_PLACEHOLDER,
        "subscriber_email": "",
        "preview_mode": False,
    }

    html_template = render_to_string(newsletter.template_path, context)
    html_template = add_utm_params(html_template, newsletter.slug)

    sent = 0
    errors = 0
    error_details = []

    connection = mail.get_connection()
    try:
        connection.open()

        for i, recipient in enumerate(recipients):
            unsub_url = (
                f"{base_url}/newsletter/unsubscribe/{recipient['unsubscribe_token']}/"
            )
            html_content = html_template.replace(
                UNSUBSCRIBE_URL_PLACEHOLDER, unsub_url
            )

            msg = EmailMultiAlternatives(
                subject=subject,
                body=f"View this newsletter in your browser. To unsubscribe: {unsub_url}",
                from_email=from_email,
                to=[recipient["email"]],
                headers={
                    "List-Unsubscribe": f"<{unsub_url}>",
                    "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
                },
                connection=connection,
            )
            msg.attach_alternative(html_content, "text/html")

            try:
                msg.send(fail_silently=False)
                sent += 1
                log(f"  Sent to {recipient['email']}")
            except Exception as e:
                errors += 1
                error_details.append({"email": recipient["email"], "error": str(e)})
                try:
                    subscriber = Subscriber.objects.get(email=recipient["email"])
                    subscriber.record_bounce()
                    log(
                        f"  FAILED {recipient['email']}: {e} "
                        f"(bounce {subscriber.bounce_count}/3)"
                    )
                except Subscriber.DoesNotExist:
                    log(f"  FAILED {recipient['email']}: {e}")

            # Batch delay
            if (i + 1) % batch_size == 0 and i + 1 < len(recipients):
                log(f"  Batch of {batch_size} sent, waiting {batch_delay}s...")
                time.sleep(batch_delay)
    finally:
        connection.close()

    # Update newsletter record (skip for test sends)
    if not test_email:
        newsletter.status = Newsletter.Status.SENT
        newsletter.sent_at = timezone.now()
        newsletter.sent_count = sent
        newsletter.save(update_fields=["status", "sent_at", "sent_count"])

    return {"sent": sent, "errors": errors, "error_details": error_details}
