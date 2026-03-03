import os
import textwrap

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import get_template
from django.template import TemplateDoesNotExist

from housegallery.newsletter.models import Newsletter


class Command(BaseCommand):
    help = "Create a new newsletter edition with a scaffolded template file."

    def add_arguments(self, parser):
        parser.add_argument("slug", type=str, help="URL-safe slug for the edition (e.g. spring-2026)")
        parser.add_argument("title", type=str, help="Newsletter title (e.g. 'Spring at the Gallery')")
        parser.add_argument("--subject", type=str, help="Email subject line (defaults to title)")

    def handle(self, *args, **options):
        slug = options["slug"]
        title = options["title"]
        subject = options.get("subject") or ""

        # Check if newsletter already exists
        if Newsletter.objects.filter(slug=slug).exists():
            raise CommandError(f"A newsletter with slug '{slug}' already exists.")

        # Check if template already exists
        template_rel = f"newsletter/editions/{slug}.html"
        try:
            get_template(template_rel)
            raise CommandError(f"Template '{template_rel}' already exists.")
        except TemplateDoesNotExist:
            pass

        # Create the DB record
        newsletter = Newsletter.objects.create(
            title=title,
            slug=slug,
            subject=subject,
        )

        # Scaffold the template file
        editions_dir = os.path.join(
            settings.BASE_DIR,
            "housegallery",
            "newsletter",
            "templates",
            "newsletter",
            "editions",
        )
        os.makedirs(editions_dir, exist_ok=True)

        template_path = os.path.join(editions_dir, f"{slug}.html")
        scaffold = textwrap.dedent(f"""\
            {{% extends "newsletter/emails/base_email.html" %}}

            {{% block preheader %}}{title}{{% endblock %}}

            {{% block content %}}
            <h1 style="font-family: 'Source Code Pro', monospace; font-weight: 300; font-size: 24px; margin: 0 0 20px;">
                {title}
            </h1>

            <p style="font-family: 'Source Code Pro', monospace; font-weight: 300; font-size: 14px; line-height: 1.8; margin: 0 0 16px;">
                Write your newsletter content here.
            </p>

            <!-- Add more sections as needed -->
            {{% endblock %}}
        """)

        with open(template_path, "w") as f:
            f.write(scaffold)

        self.stdout.write(self.style.SUCCESS(
            f"Created newsletter '{title}' (slug: {slug})"
        ))
        self.stdout.write(f"  DB record: Newsletter #{newsletter.pk}")
        self.stdout.write(f"  Template:  {template_path}")
        self.stdout.write(f"  Preview:   /newsletter/preview/{slug}/")
