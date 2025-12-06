"""
Management command to import artworks from a CSV file.

Supports both local files and Google Cloud Storage URLs (gs://bucket/path/file.csv).
"""

import csv
import tempfile
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from housegallery.artworks.models import Artwork, ArtworkArtist
from housegallery.artists.models import Artist
from housegallery.exhibitions.models import ExhibitionPage, ExhibitionArtwork


class Command(BaseCommand):
    help = 'Import artworks from a CSV file (local path or gs:// URL)'

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
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip artworks that already exist (matched by title and artist)',
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']
        skip_existing = options['skip_existing']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('Running in DRY-RUN mode - no changes will be made')
            )

        # Cache for artists and exhibitions to avoid repeated lookups
        artist_cache = {}
        exhibition_cache = {}

        # Counters
        created_count = 0
        skipped_count = 0
        error_count = 0

        # Handle GCS URLs or local files
        try:
            if csv_file.startswith('gs://'):
                local_path = self._download_from_gcs(csv_file)
                if not local_path:
                    return
            else:
                local_path = csv_file

            with open(local_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file}'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading CSV: {e}'))
            return

        self.stdout.write(f'Found {len(rows)} rows in CSV file')
        self.stdout.write('')

        for row_num, row in enumerate(rows, start=2):  # Start at 2 to account for header
            title = row.get('Title', '').strip()
            artist_name = row.get('Artist', '').strip()
            date_str = row.get('Date', '').strip()
            size = row.get('Size', '').strip()
            materials_str = row.get('Materials', '').strip()
            description = row.get('Description', '').strip()
            exhibition_name = row.get('Exhibitions', '').strip()

            # Skip rows with empty title (these are likely empty rows or notes)
            if not title:
                self.stdout.write(f'  Row {row_num}: Skipping (no title)')
                skipped_count += 1
                continue

            # Check for existing artwork if skip_existing is enabled
            if skip_existing and artist_name:
                artist = self._get_or_create_artist(artist_name, artist_cache, dry_run)
                if artist:
                    existing = Artwork.objects.filter(
                        title__icontains=title,
                        artists=artist
                    ).exists()
                    if existing:
                        self.stdout.write(f'  Row {row_num}: Skipping "{title}" (already exists)')
                        skipped_count += 1
                        continue

            # Process the row
            try:
                if not dry_run:
                    with transaction.atomic():
                        artwork = self._create_artwork(
                            title=title,
                            artist_name=artist_name,
                            date_str=date_str,
                            size=size,
                            materials_str=materials_str,
                            description=description,
                            exhibition_name=exhibition_name,
                            artist_cache=artist_cache,
                            exhibition_cache=exhibition_cache,
                            dry_run=dry_run,
                        )
                        self.stdout.write(
                            self.style.SUCCESS(f'  Row {row_num}: Created "{title}"')
                        )
                else:
                    # Dry run - just show what would be created
                    self._create_artwork(
                        title=title,
                        artist_name=artist_name,
                        date_str=date_str,
                        size=size,
                        materials_str=materials_str,
                        description=description,
                        exhibition_name=exhibition_name,
                        artist_cache=artist_cache,
                        exhibition_cache=exhibition_cache,
                        dry_run=dry_run,
                    )
                    self.stdout.write(f'  Row {row_num}: Would create "{title}"')

                created_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  Row {row_num}: Error creating "{title}": {e}')
                )
                error_count += 1

        # Summary
        self.stdout.write('')
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY-RUN Complete: Would create {created_count} artworks, '
                    f'skipped {skipped_count}, errors {error_count}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Import complete: Created {created_count} artworks, '
                    f'skipped {skipped_count}, errors {error_count}'
                )
            )

    def _download_from_gcs(self, gcs_url):
        """Download a file from Google Cloud Storage to a temp file."""
        try:
            from google.cloud import storage
        except ImportError:
            self.stdout.write(
                self.style.ERROR(
                    'google-cloud-storage is not installed. '
                    'Install it with: pip install google-cloud-storage'
                )
            )
            return None

        # Parse gs://bucket/path/to/file.csv
        path = gcs_url[5:]  # Remove 'gs://'
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

            # Download to a temp file
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

    def _get_or_create_artist(self, artist_name, cache, dry_run):
        """Get or create an artist by name, using cache for efficiency."""
        if not artist_name:
            return None

        if artist_name in cache:
            return cache[artist_name]

        if dry_run:
            # In dry run, try to find existing artist
            artist = Artist.objects.filter(name__iexact=artist_name).first()
            if artist:
                cache[artist_name] = artist
                return artist
            # In dry run, return None but note that artist would be created
            self.stdout.write(f'    Would create artist: "{artist_name}"')
            cache[artist_name] = None
            return None

        artist, created = Artist.objects.get_or_create(
            name__iexact=artist_name,
            defaults={'name': artist_name}
        )
        if created:
            self.stdout.write(f'    Created artist: "{artist_name}"')
        cache[artist_name] = artist
        return artist

    def _get_exhibition(self, exhibition_name, cache, dry_run):
        """Get an exhibition by title, using cache for efficiency."""
        if not exhibition_name:
            return None

        if exhibition_name in cache:
            return cache[exhibition_name]

        # Search for exhibition page by title (case-insensitive)
        exhibition = ExhibitionPage.objects.filter(
            title__icontains=exhibition_name
        ).first()

        if not exhibition:
            # Try searching by slug
            slug = exhibition_name.lower().replace(' ', '-')[:50]
            exhibition = ExhibitionPage.objects.filter(slug__icontains=slug).first()

        if exhibition:
            cache[exhibition_name] = exhibition
        else:
            self.stdout.write(
                self.style.WARNING(f'    Exhibition not found: "{exhibition_name}"')
            )
            cache[exhibition_name] = None

        return cache[exhibition_name]

    def _parse_date(self, date_str):
        """Parse a year string into a timezone-aware datetime object."""
        if not date_str:
            return None

        try:
            # Try parsing as just a year
            year = int(date_str)
            if 1900 <= year <= 2100:
                return timezone.make_aware(datetime(year, 1, 1))
        except ValueError:
            pass

        # Try parsing as full date
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
            try:
                dt = datetime.strptime(date_str, fmt)
                return timezone.make_aware(dt)
            except ValueError:
                continue

        return None

    def _parse_materials(self, materials_str):
        """Parse a comma-separated materials string into a list of tag names."""
        if not materials_str:
            return []

        # Split on comma and/or ampersand, then clean up
        materials = []
        for material in materials_str.replace('&', ',').split(','):
            material = material.strip()
            if material:
                materials.append(material)

        return materials

    def _create_artwork(
        self,
        title,
        artist_name,
        date_str,
        size,
        materials_str,
        description,
        exhibition_name,
        artist_cache,
        exhibition_cache,
        dry_run,
    ):
        """Create an artwork with all its relationships."""
        if dry_run:
            # In dry run, just validate and show what would happen
            date = self._parse_date(date_str)
            materials = self._parse_materials(materials_str)
            artist = self._get_or_create_artist(artist_name, artist_cache, dry_run)
            exhibition = self._get_exhibition(exhibition_name, exhibition_cache, dry_run)

            self.stdout.write(f'    Title: "{title}"')
            if artist_name:
                self.stdout.write(f'    Artist: "{artist_name}"')
            if date:
                self.stdout.write(f'    Date: {date.year}')
            if size:
                self.stdout.write(f'    Size: "{size}"')
            if materials:
                self.stdout.write(f'    Materials: {materials}')
            if exhibition:
                self.stdout.write(f'    Exhibition: "{exhibition.title}"')

            return None

        # Create the artwork as a draft (live=False)
        artwork = Artwork(
            title=title,
            description=description,
            size=size,
            date=self._parse_date(date_str),
            live=False,  # Create as draft
        )
        artwork.save()

        # Add materials as tags (must save after for ClusterTaggableManager)
        materials = self._parse_materials(materials_str)
        if materials:
            artwork.materials.add(*materials)
            artwork.save()

        # Link to artist
        artist = self._get_or_create_artist(artist_name, artist_cache, dry_run)
        if artist:
            ArtworkArtist.objects.create(
                artwork=artwork,
                artist=artist,
            )

        # Link to exhibition
        exhibition = self._get_exhibition(exhibition_name, exhibition_cache, dry_run)
        if exhibition:
            ExhibitionArtwork.objects.get_or_create(
                page=exhibition,
                artwork=artwork,
            )

        return artwork
