"""
Management command to populate artwork relationships for existing exhibition images.
"""

from django.core.management.base import BaseCommand
from housegallery.exhibitions.models import ExhibitionImage


class Command(BaseCommand):
    help = 'Update artwork relationships for existing exhibition images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Running in DRY-RUN mode - no changes will be made')
            )
        
        # Get all exhibition images
        exhibition_images = ExhibitionImage.objects.all()
        total_count = exhibition_images.count()
        updated_count = 0
        
        self.stdout.write(f'Processing {total_count} exhibition images...')
        
        for exhibition_image in exhibition_images:
            # Detect artwork relationship
            detected_artwork = exhibition_image.detect_related_artwork()
            
            if detected_artwork:
                if exhibition_image.related_artwork != detected_artwork:
                    if not dry_run:
                        exhibition_image.related_artwork = detected_artwork
                        exhibition_image.save(update_fields=['related_artwork'])
                    
                    updated_count += 1
                    self.stdout.write(
                        f'  • Image {exhibition_image.id} linked to artwork: {detected_artwork.title}'
                    )
                else:
                    self.stdout.write(
                        f'  • Image {exhibition_image.id} already linked to: {detected_artwork.title}'
                    )
            else:
                if exhibition_image.related_artwork:
                    if not dry_run:
                        exhibition_image.related_artwork = None
                        exhibition_image.save(update_fields=['related_artwork'])
                    
                    self.stdout.write(
                        f'  • Image {exhibition_image.id} cleared previous artwork link'
                    )
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY-RUN: Would have updated {updated_count} of {total_count} exhibition images'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {updated_count} of {total_count} exhibition images'
                )
            )