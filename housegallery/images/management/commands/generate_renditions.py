from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from housegallery.images.models import CustomImage, Rendition


# Standard rendition specs used across the site
STANDARD_RENDITIONS = [
    # Legacy template tag renditions
    'width-400',
    'width-400|format-webp',
    'width-1200',
    'width-1200|format-webp',
    # New helper method renditions
    'width-1440|format-webp|webpquality-85',  # get_web_optimized()
    'fill-300x300|format-webp|webpquality-90',  # get_thumbnail()
]

# Note: get_display_optimized() is handled separately as it's dynamic based on image size


class Command(BaseCommand):
    help = 'Generate standard renditions for images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be generated without actually generating',
        )
        parser.add_argument(
            '--missing-only',
            action='store_true',
            help='Only generate renditions for images missing standard sizes',
        )
        parser.add_argument(
            '--image-id',
            type=int,
            help='Generate renditions for a specific image ID',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of images to process before reporting progress (default: 50)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        missing_only = options['missing_only']
        image_id = options.get('image_id')
        batch_size = options['batch_size']

        # Build queryset
        if image_id:
            images = CustomImage.objects.filter(pk=image_id)
            if not images.exists():
                self.stdout.write(self.style.ERROR(f'Image {image_id} not found'))
                return
        elif missing_only:
            # Find images missing any standard rendition
            images = self._get_images_missing_renditions()
        else:
            images = CustomImage.objects.all()

        total = images.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('All images have standard renditions!'))
            return

        if dry_run:
            self.stdout.write(f'Would generate renditions for {total} images:')
            for spec in STANDARD_RENDITIONS:
                self.stdout.write(f'  - {spec}')
            return

        self.stdout.write(f'Generating renditions for {total} images...')

        generated_count = 0
        error_count = 0

        for i, image in enumerate(images.iterator()):
            try:
                renditions_created = self._generate_for_image(image)
                generated_count += renditions_created

                if (i + 1) % batch_size == 0:
                    self.stdout.write(
                        f'Progress: {i + 1}/{total} images '
                        f'({generated_count} renditions created)'
                    )

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Failed for image {image.id} ({image.title}): {e}')
                )

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Completed: {total} images processed, '
            f'{generated_count} renditions created, '
            f'{error_count} errors'
        ))

    def _get_images_missing_renditions(self):
        """Find images that don't have all standard renditions."""
        # Get images with fewer than expected renditions
        # (This is a heuristic - checks count, not exact specs)
        expected_count = len(STANDARD_RENDITIONS)

        return CustomImage.objects.annotate(
            rendition_count=Count('renditions')
        ).filter(
            Q(rendition_count__lt=expected_count)
        )

    def _generate_for_image(self, image):
        """Generate missing renditions for a single image. Returns count created."""
        created = 0

        # Get existing rendition specs for this image
        existing_specs = set(
            image.renditions.values_list('filter_spec', flat=True)
        )

        for spec in STANDARD_RENDITIONS:
            if spec not in existing_specs:
                try:
                    image.get_rendition(spec)
                    created += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Could not create {spec} for image {image.id}: {e}'
                        )
                    )

        # Handle get_display_optimized() - dynamic based on image dimensions
        try:
            image.get_display_optimized()
            # Note: May or may not create a new rendition depending on existing specs
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f'  Could not create display_optimized for image {image.id}: {e}'
                )
            )

        return created