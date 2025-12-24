"""
Management command to import Joseph Blake's artworks from onequicktrick.com.

Downloads artwork metadata and images, creates Artwork records linked to the
Joseph Blake artist, and associates images with each artwork.
"""

import io
import json
import re
import tempfile
import urllib.request
from datetime import datetime

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from housegallery.artists.models import Artist
from housegallery.artworks.models import Artwork, ArtworkArtist, ArtworkImage
from housegallery.images.models import CustomImage


# Base URL for the onequicktrick.com site
BASE_URL = "https://onequicktrick.com"
PAYLOAD_URL = f"{BASE_URL}/_nuxt/static/1664001531/artwork/payload.js"

# Image srcsets extracted from the HTML (in order matching payload data)
# These are the highest resolution versions (1240px or largest available)
IMAGE_URLS = [
    "/_nuxt/3c773ea78ca05f5332e8f1b843df80d9-1240.png",  # Page 14
    "/_nuxt/63953807cc923eae726e6ae1c0fe45f8-1240.png",  # On a walk
    "/_nuxt/563688979de4bc4237a462898abe198e-1240.png",  # Transgressions1
    "/_nuxt/7d4118210f69aad08dcc04541cbf39e5-1240.png",  # Transgressions2
    "/_nuxt/5c6213ce3cb7ccb4bdf5204cabd0c47b-1152.png",  # A Hypertext Document...
    "/_nuxt/f2a55aaabec880f1fba831c90e45d042-1240.png",  # Page is broken
    "/_nuxt/db193484676eb14e80fcabbbaf555a7b-1240.png",  # Bodyheat1
    "/_nuxt/205dbcc63fee186122dac20256379d31-1240.png",  # Bodyheat2
    "/_nuxt/7d01f64a7d83cb41c65c8b83cfde76e8-1240.png",  # Clutch
    "/_nuxt/59b9a6a0af7163f72f6322554de3d9ea-1240.png",  # Earthform
    "/_nuxt/c0d3620bf38cb08dcdfd8814348676f6-1240.png",  # Hayshed
    "/_nuxt/b8f601051c0847305b6a3780baae417e-1240.png",  # MAW
    "/_nuxt/c0b0a87729f0b397cad5e585180b6c28-1240.png",  # Mantra
    "/_nuxt/9f3e8c47a22b439cd43ffe9133f682f4-1240.png",  # Fell out of ground...
    "/_nuxt/f198522818ea9f63d1a1c9adaf6858c4-1240.png",  # Gallop
    "/_nuxt/f4628e4cdfe44e5ef1541d5ff70bb47b-1240.png",  # Incandescent Daytime
    "/_nuxt/54a8dd935dd469c756eb4537680ad1d8-1240.png",  # Shades of a Garden...
    "/_nuxt/ffac3ea674002066775a013874c2e379-1240.png",  # The Show Title
    "/_nuxt/f7c1c06b21e923551c0e3a2e06d0fc13-1240.png",  # The Vain Image
    "/_nuxt/e1b787204d6a9237f1dcd7b8f8d48366-1240.png",  # Troubled
]


class Command(BaseCommand):
    help = "Import Joseph Blake's artworks from onequicktrick.com"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run in dry-run mode without making changes",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Skip artworks that already exist (matched by title and artist)",
        )
        parser.add_argument(
            "--skip-images",
            action="store_true",
            help="Import metadata only, skip image download",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        skip_existing = options["skip_existing"]
        skip_images = options["skip_images"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Running in DRY-RUN mode - no changes will be made")
            )

        # Get or validate Joseph Blake artist exists
        try:
            artist = Artist.objects.get(name__icontains="Joseph Blake")
            self.stdout.write(f"Found artist: {artist.name} (ID: {artist.pk})")
        except Artist.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    "Joseph Blake artist not found. Please create the artist first."
                )
            )
            return
        except Artist.MultipleObjectsReturned:
            artist = Artist.objects.filter(name__icontains="Joseph Blake").first()
            self.stdout.write(
                self.style.WARNING(
                    f"Multiple artists found matching 'Joseph Blake', using: {artist.name}"
                )
            )

        # Fetch and parse artwork data
        self.stdout.write("Fetching artwork data from onequicktrick.com...")
        artworks_data = self._fetch_artwork_data()

        if not artworks_data:
            self.stdout.write(self.style.ERROR("Failed to fetch artwork data"))
            return

        self.stdout.write(f"Found {len(artworks_data)} artworks to import")
        self.stdout.write("")

        # Counters
        created_count = 0
        skipped_count = 0
        error_count = 0

        for idx, artwork_data in enumerate(artworks_data):
            title = artwork_data.get("title", "")
            description = artwork_data.get("description", "")
            date_year = artwork_data.get("date")
            size = artwork_data.get("size", "")

            if not title:
                self.stdout.write(f"  #{idx + 1}: Skipping (no title)")
                skipped_count += 1
                continue

            # Check for existing artwork
            if skip_existing:
                existing = Artwork.objects.filter(
                    title__iexact=title, artists=artist
                ).exists()
                if existing:
                    self.stdout.write(f'  #{idx + 1}: Skipping "{title}" (already exists)')
                    skipped_count += 1
                    continue

            # Get image URL for this artwork
            image_url = IMAGE_URLS[idx] if idx < len(IMAGE_URLS) else None

            try:
                if dry_run:
                    self._preview_artwork(
                        idx, title, description, date_year, size, image_url
                    )
                else:
                    with transaction.atomic():
                        self._create_artwork(
                            idx=idx,
                            title=title,
                            description=description,
                            date_year=date_year,
                            size=size,
                            image_url=image_url,
                            artist=artist,
                            skip_images=skip_images,
                        )
                        self.stdout.write(
                            self.style.SUCCESS(f'  #{idx + 1}: Created "{title}"')
                        )

                created_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  #{idx + 1}: Error creating "{title}": {e}')
                )
                error_count += 1

        # Summary
        self.stdout.write("")
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"DRY-RUN Complete: Would create {created_count} artworks, "
                    f"skipped {skipped_count}, errors {error_count}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Import complete: Created {created_count} artworks, "
                    f"skipped {skipped_count}, errors {error_count}"
                )
            )

    def _fetch_artwork_data(self):
        """Fetch and parse the JSONP payload from onequicktrick.com."""
        try:
            with urllib.request.urlopen(PAYLOAD_URL) as response:
                content = response.read().decode("utf-8")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fetching payload: {e}"))
            return None

        # The payload is JSONP with variable substitution
        # We need to evaluate it to get the actual data
        # Extract the function body and evaluate the variables

        # Parse the JSONP: __NUXT_JSONP__("/artwork", (function(...){return {...}}(...)))
        match = re.search(r"return ({.*?})\}\((.*?)\)\)", content, re.DOTALL)
        if not match:
            self.stdout.write(self.style.ERROR("Could not parse JSONP payload"))
            return None

        template = match.group(1)
        args_str = match.group(2)

        # Parse the arguments (they're comma-separated values)
        # This is tricky because strings contain commas
        args = self._parse_jsonp_args(args_str)

        # Variable names in order: a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z, A, B, ...
        var_names = list("abcdefghijklmnopqrstuvwxyz") + [
            chr(ord("A") + i) for i in range(26)
        ]

        # Create substitution map
        var_map = {}
        for i, arg in enumerate(args):
            if i < len(var_names):
                var_map[var_names[i]] = arg

        # Substitute variables in template
        # We need to be careful to only replace standalone variable names
        result = template

        # Replace variable references with their values
        # Sort by length descending to avoid partial replacements
        for var_name in sorted(var_map.keys(), key=len, reverse=True):
            value = var_map[var_name]
            # Only replace if it's a standalone variable (not part of a string)
            if isinstance(value, str):
                replacement = json.dumps(value)
            elif isinstance(value, bool):
                replacement = "true" if value else "false"
            elif value is None:
                replacement = "null"
            else:
                replacement = str(value)

            # Replace variable references (word boundaries)
            result = re.sub(rf"\b{var_name}\b", replacement, result)

        # Clean up the JSON
        result = result.replace("void 0", "null")

        try:
            data = json.loads(result)
            return data.get("data", [{}])[0].get("artworks", [])
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"JSON parse error: {e}"))
            # Try a simpler approach - manually extract the data
            return self._fallback_parse(content)

    def _parse_jsonp_args(self, args_str):
        """Parse the comma-separated arguments from JSONP, handling strings properly."""
        args = []
        current = ""
        in_string = False
        string_char = None
        escape_next = False
        paren_depth = 0

        for char in args_str:
            if escape_next:
                current += char
                escape_next = False
                continue

            if char == "\\":
                current += char
                escape_next = True
                continue

            if char in "\"'" and not in_string:
                in_string = True
                string_char = char
                current += char
                continue

            if char == string_char and in_string:
                in_string = False
                string_char = None
                current += char
                continue

            if char == "(" and not in_string:
                paren_depth += 1
                current += char
                continue

            if char == ")" and not in_string:
                paren_depth -= 1
                current += char
                continue

            if char == "," and not in_string and paren_depth == 0:
                args.append(self._parse_arg_value(current.strip()))
                current = ""
                continue

            current += char

        if current.strip():
            args.append(self._parse_arg_value(current.strip()))

        return args

    def _parse_arg_value(self, value):
        """Parse a single argument value."""
        if value == "true":
            return True
        if value == "false":
            return False
        if value == "void 0" or value == "null":
            return None
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1].replace('\\"', '"').replace("\\u002F", "/")
        if value.startswith("'") and value.endswith("'"):
            return value[1:-1].replace("\\'", "'").replace("\\u002F", "/")
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    def _fallback_parse(self, content):
        """Fallback parser if JSON parsing fails - extract data directly."""
        artworks = []

        # Extract artwork objects using regex
        # Looking for patterns like: {slug:"...",title:"...",date:YYYY,size:"..."}
        pattern = r'\{slug:["\']([^"\']+)["\'].*?title:["\']([^"\']+)["\'].*?date:(\d+).*?size:["\']([^"\']+)["\'].*?description:["\']([^"\']*)["\']'

        # Simpler approach: extract the hardcoded data we know exists
        known_artworks = [
            {
                "title": "Page 14",
                "date": 2019,
                "size": '25" x 6" x 1"',
                "description": "book, handmade paper, wire inclusion, toner transfer",
            },
            {
                "title": "On a walk",
                "date": 2019,
                "size": '5" x 6"',
                "description": "handmade paper, wire inclusion, toner transfer",
            },
            {
                "title": "Transgressions1",
                "date": 2019,
                "size": '30" x 22"',
                "description": "handmade paper, wire inclusion, collagraph, toner transfer",
            },
            {
                "title": "Transgressions2",
                "date": 2019,
                "size": '30" x 22"',
                "description": "handmade paper, wire inclusion, collagraph, toner transfer",
            },
            {
                "title": "A Hypertext Document to the Worldwide Web",
                "date": 2019,
                "size": '14" x 6" x 1"',
                "description": "book, handmade paper, wire inclusion, toner transfer",
            },
            {
                "title": "Page is broken",
                "date": 2020,
                "size": "8' x 4'",
                "description": "handmade paper, toner transfer, chains",
            },
            {
                "title": "Bodyheat1",
                "date": 2021,
                "size": '17" x 25"',
                "description": "recycled plastic, shipping labels, direct thermal print",
            },
            {
                "title": "Bodyheat2",
                "date": 2021,
                "size": '22" x 25"',
                "description": "recycled plastic, shipping labels, direct thermal print",
            },
            {
                "title": "Clutch",
                "date": 2021,
                "size": "7' x 6'",
                "description": "receipt roll, direct thermal print",
            },
            {
                "title": "Earthform",
                "date": 2021,
                "size": "3' x 3' x 5'",
                "description": "receipt roll, direct thermal print",
            },
            {
                "title": "Hayshed",
                "date": 2021,
                "size": "4' x 4' x 6'",
                "description": "recycled wood, receipt roll, direct thermal print",
            },
            {
                "title": "MAW",
                "date": 2021,
                "size": '56" x 40"',
                "description": "receipt roll, direct thermal print",
            },
            {
                "title": "Mantra",
                "date": 2021,
                "size": '3.125" x 18"',
                "description": "receipt roll, direct thermal print",
            },
            {
                "title": "Fell out of ground hole to be further in...",
                "date": 2022,
                "size": "10' x 14'",
                "description": "receipt roll, direct thermal print",
            },
            {
                "title": "Gallop",
                "date": 2022,
                "size": '19" x 9"',
                "description": "receipt roll, direct thermal print",
            },
            {
                "title": "Incandescent Daytime",
                "date": 2022,
                "size": "3' x 4'",
                "description": "wood, handmade paper, toner print",
            },
            {
                "title": "Shades of a Garden Campus",
                "date": 2022,
                "size": "10' x 10' x 10'",
                "description": "pvc, cement, receipt roll, direct thermal print",
            },
            {
                "title": "The Show Title",
                "date": 2022,
                "size": '29" x 28"',
                "description": "drywall, paint, receipt roll, direct thermal print, torch, one big nail",
            },
            {
                "title": "The Vain Image",
                "date": 2022,
                "size": '84" x 84" x 4"',
                "description": "recycled wood, receipt roll, direct thermal print",
            },
            {
                "title": "Troubled",
                "date": 2022,
                "size": "18' x 10'",
                "description": "receipt roll, direct thermal print",
            },
        ]

        return known_artworks

    def _preview_artwork(self, idx, title, description, date_year, size, image_url):
        """Preview what would be created in dry-run mode."""
        self.stdout.write(f'  #{idx + 1}: Would create "{title}"')
        self.stdout.write(f"       Date: {date_year}")
        self.stdout.write(f"       Size: {size}")
        if description:
            self.stdout.write(f"       Materials: {description}")
        if image_url:
            self.stdout.write(f"       Image: {BASE_URL}{image_url}")

    def _create_artwork(
        self,
        idx,
        title,
        description,
        date_year,
        size,
        image_url,
        artist,
        skip_images,
    ):
        """Create an artwork with its image and relationships."""
        # Parse date
        artwork_date = None
        if date_year:
            artwork_date = timezone.make_aware(datetime(int(date_year), 1, 1))

        # Parse materials from description
        materials = []
        if description:
            materials = [m.strip() for m in description.replace("/", ",").split(",")]

        # Create the artwork (published)
        artwork = Artwork(
            title=title,
            size=size,
            date=artwork_date,
            live=True,
        )
        artwork.save()

        # Add materials as tags
        if materials:
            artwork.materials.add(*materials)
            artwork.save()

        # Link to artist
        ArtworkArtist.objects.create(artwork=artwork, artist=artist)

        # Download and create image
        if not skip_images and image_url:
            try:
                image = self._download_and_create_image(
                    image_url=f"{BASE_URL}{image_url}",
                    title=title,
                    alt=f"{title} - {description}" if description else title,
                )
                if image:
                    ArtworkImage.objects.create(
                        artwork=artwork,
                        image=image,
                        sort_order=0,
                    )
                    self.stdout.write(f"       Image downloaded and linked")
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"       Failed to download image: {e}")
                )

        return artwork

    def _download_and_create_image(self, image_url, title, alt):
        """Download an image from URL and create a CustomImage."""
        self.stdout.write(f"       Downloading: {image_url}")

        # Create a request with headers to avoid 403 errors
        request = urllib.request.Request(
            image_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            },
        )

        with urllib.request.urlopen(request, timeout=30) as response:
            image_data = response.read()

        # Determine file extension from URL
        ext = ".png"
        if ".jpg" in image_url or ".jpeg" in image_url:
            ext = ".jpg"
        elif ".webp" in image_url:
            ext = ".webp"

        # Create filename from title
        safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")[:50]
        filename = f"{safe_title}{ext}"

        # Create in-memory file
        image_file = io.BytesIO(image_data)
        content_type = "image/png" if ext == ".png" else "image/jpeg"

        uploaded_file = InMemoryUploadedFile(
            image_file,
            "ImageField",
            filename,
            content_type,
            len(image_data),
            None,
        )

        # Create CustomImage
        image = CustomImage(
            title=title,
            file=uploaded_file,
            alt=alt[:510] if alt else title[:510],
            credit="Joseph Blake",
        )
        image.save()

        return image
