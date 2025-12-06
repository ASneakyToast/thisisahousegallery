"""
Management command to fix materials for imported artworks.

Re-reads the CSV and applies materials that were missed during initial import.
"""

import csv
import tempfile

from django.core.management.base import BaseCommand

from housegallery.artworks.models import Artwork


class Command(BaseCommand):
    help = 'Fix materials for imported artworks by re-reading from CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to CSV file (local path or gs://bucket/path/file.csv)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode without making changes',
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('Running in DRY-RUN mode - no changes will be made')
            )

        # Handle GCS URLs
        if csv_file.startswith('gs://'):
            local_path = self._download_from_gcs(csv_file)
            if not local_path:
                return
        else:
            local_path = csv_file

        updated = 0
        skipped = 0

        try:
            with open(local_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    title = row.get('Title', '').strip()
                    materials_str = row.get('Materials', '').strip()

                    if not title or not materials_str:
                        continue

                    # Find the artwork (draft only)
                    artwork = Artwork.objects.filter(
                        title__icontains=title,
                        live=False
                    ).first()

                    if not artwork:
                        skipped += 1
                        continue

                    # Check if materials already set
                    if artwork.materials.exists():
                        self.stdout.write(f'  Skipping "{title}" (already has materials)')
                        skipped += 1
                        continue

                    # Parse materials
                    materials = [
                        m.strip()
                        for m in materials_str.replace('&', ',').split(',')
                        if m.strip()
                    ]

                    if materials:
                        if not dry_run:
                            artwork.materials.add(*materials)
                            artwork.save()
                        updated += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  Updated "{title}" -> {materials}')
                        )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            return

        self.stdout.write('')
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY-RUN Complete: Would update {updated}, skipped {skipped}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Complete: Updated {updated}, skipped {skipped}'
                )
            )

    def _download_from_gcs(self, gcs_url):
        """Download a file from Google Cloud Storage to a temp file."""
        try:
            from google.cloud import storage
        except ImportError:
            self.stdout.write(
                self.style.ERROR('google-cloud-storage is not installed.')
            )
            return None

        path = gcs_url[5:]
        parts = path.split('/', 1)
        if len(parts) != 2:
            self.stdout.write(
                self.style.ERROR(f'Invalid GCS URL format: {gcs_url}')
            )
            return None

        bucket_name, blob_path = parts

        self.stdout.write(f'Downloading from GCS: {gcs_url}')

        try:
            from django.conf import settings
            project_id = getattr(settings, 'GS_PROJECT_ID', None)
            client = storage.Client(project=project_id)
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_path)

            temp_file = tempfile.NamedTemporaryFile(
                mode='wb',
                suffix='.csv',
                delete=False
            )
            blob.download_to_file(temp_file)
            temp_file.close()

            self.stdout.write(
                self.style.SUCCESS(f'Downloaded to: {temp_file.name}')
            )
            return temp_file.name

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error downloading from GCS: {e}')
            )
            return None
