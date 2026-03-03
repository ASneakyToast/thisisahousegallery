import time

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.utils import timezone

from housegallery.newsletter.models import Newsletter, Subscriber


class Command(BaseCommand):
    help = "Send a newsletter edition to all confirmed subscribers."

    def add_arguments(self, parser):
        parser.add_argument("slug", type=str, help="Newsletter edition slug to send")
        parser.add_argument(
            "--test",
            type=str,
            metavar="EMAIL",
            help="Send only to this email address (for testing)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be sent without actually sending",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Number of emails per batch (default: 50)",
        )
        parser.add_argument(
            "--batch-delay",
            type=float,
            default=2.0,
            help="Seconds to wait between batches (default: 2.0)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Send even if newsletter was already sent",
        )

    def handle(self, *args, **options):
        slug = options["slug"]
        test_email = options.get("test")
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]
        batch_delay = options["batch_delay"]
        force = options["force"]

        try:
            newsletter = Newsletter.objects.get(slug=slug)
        except Newsletter.DoesNotExist:
            raise CommandError(f"No newsletter found with slug '{slug}'.")

        if newsletter.status == Newsletter.Status.SENT and not force:
            raise CommandError(
                f"Newsletter '{slug}' was already sent on {newsletter.sent_at}. "
                "Use --force to send again."
            )

        from_email = getattr(
            settings, "DEFAULT_FROM_EMAIL", "noreply@thisisahousegallery.com"
        )
        subject = newsletter.effective_subject

        # Determine recipients
        if test_email:
            recipients = [{"email": test_email, "unsubscribe_token": "test-token"}]
            self.stdout.write(f"TEST MODE: sending to {test_email}")
        else:
            subscribers = Subscriber.objects.filter(
                confirmed=True, unsubscribed_at__isnull=True
            )
            recipients = list(subscribers.values("email", "unsubscribe_token"))
            self.stdout.write(f"Sending to {len(recipients)} subscribers")

        if not recipients:
            self.stdout.write(self.style.WARNING("No recipients found."))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no emails will be sent"))
            for r in recipients:
                self.stdout.write(f"  Would send to: {r['email']}")
            return

        sent = 0
        errors = 0

        for i, recipient in enumerate(recipients):
            # Build per-recipient unsubscribe URL
            unsub_url = f"{_get_base_url()}/newsletter/unsubscribe/{recipient['unsubscribe_token']}/"

            context = {
                "newsletter": newsletter,
                "unsubscribe_url": unsub_url,
                "subscriber_email": recipient["email"],
                "preview_mode": False,
            }

            try:
                html_content = render_to_string(newsletter.template_path, context)
            except Exception as e:
                raise CommandError(f"Error rendering template: {e}")

            msg = EmailMultiAlternatives(
                subject=subject,
                body=f"View this newsletter in your browser. To unsubscribe: {unsub_url}",
                from_email=from_email,
                to=[recipient["email"]],
                headers={
                    "List-Unsubscribe": f"<{unsub_url}>",
                    "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
                },
            )
            msg.attach_alternative(html_content, "text/html")

            try:
                msg.send(fail_silently=False)
                sent += 1
                self.stdout.write(f"  Sent to {recipient['email']}")
            except Exception as e:
                errors += 1
                self.stderr.write(f"  FAILED {recipient['email']}: {e}")

            # Batch delay
            if (i + 1) % batch_size == 0 and i + 1 < len(recipients):
                self.stdout.write(
                    f"  Batch of {batch_size} sent, waiting {batch_delay}s..."
                )
                time.sleep(batch_delay)

        # Update newsletter record (skip for test sends)
        if not test_email:
            newsletter.status = Newsletter.Status.SENT
            newsletter.sent_at = timezone.now()
            newsletter.sent_count = sent
            newsletter.save(update_fields=["status", "sent_at", "sent_count"])

        self.stdout.write(
            self.style.SUCCESS(f"Done. Sent: {sent}, Errors: {errors}")
        )


def _get_base_url():
    """Get the site base URL from Wagtail settings or fallback."""
    try:
        from wagtail.models import Site

        site = Site.objects.filter(is_default_site=True).first()
        if site:
            return site.root_url.rstrip("/")
    except Exception:
        pass
    return "https://thisisahousegallery.com"
