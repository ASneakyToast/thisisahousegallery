from django.core.management.base import BaseCommand, CommandError

from housegallery.newsletter.models import Newsletter
from housegallery.newsletter.services import send_newsletter_edition


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
        parser.add_argument(
            "--include-bounced",
            action="store_true",
            help="Include subscribers suppressed due to bounces",
        )

    def handle(self, *args, **options):
        slug = options["slug"]

        try:
            newsletter = Newsletter.objects.get(slug=slug)
        except Newsletter.DoesNotExist:
            raise CommandError(f"No newsletter found with slug '{slug}'.")

        try:
            result = send_newsletter_edition(
                newsletter,
                test_email=options.get("test"),
                dry_run=options["dry_run"],
                batch_size=options["batch_size"],
                batch_delay=options["batch_delay"],
                force=options["force"],
                include_bounced=options["include_bounced"],
                log_callback=lambda msg: self.stdout.write(msg),
            )
        except ValueError as e:
            raise CommandError(str(e))

        if result.get("no_recipients"):
            self.stdout.write(self.style.WARNING("No recipients found."))
            return

        if result.get("dry_run"):
            self.stdout.write(self.style.WARNING("DRY RUN - no emails will be sent"))
            for email in result["would_send_to"]:
                self.stdout.write(f"  Would send to: {email}")
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Sent: {result['sent']}, Errors: {result['errors']}"
            )
        )
