from django.core.management.base import BaseCommand
from housegallery.images.models import CustomImage


class Command(BaseCommand):
    help = 'Generate standard renditions for all existing images'

    def handle(self, *args, **options):
        images = CustomImage.objects.all()
        total = images.count()
        
        self.stdout.write(f'Generating renditions for {total} images...')
        
        for i, image in enumerate(images):
            try:
                # Generate standard renditions
                image.get_rendition('width-400')
                image.get_rendition('width-400|format-webp')
                image.get_rendition('width-1200')
                image.get_rendition('width-1200|format-webp')
                
                if (i + 1) % 10 == 0:
                    self.stdout.write(f'Processed {i + 1}/{total} images')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to generate renditions for image {image.id}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully generated renditions for {total} images')
        )