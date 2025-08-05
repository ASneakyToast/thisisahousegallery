from django.core.management.base import BaseCommand, CommandError
from housegallery.api.models import APIKey
from housegallery.artists.models import Artist


class Command(BaseCommand):
    help = 'Create an API key for an artist'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'artist_name',
            type=str,
            help='Name of the artist (must match exactly)'
        )
        parser.add_argument(
            '--name',
            type=str,
            default=None,
            help='Name for the API key (defaults to "API Key for [artist]")'
        )
        parser.add_argument(
            '--rate-limit',
            type=int,
            default=1000,
            help='Rate limit per hour (default: 1000)'
        )
    
    def handle(self, *args, **options):
        artist_name = options['artist_name']
        
        try:
            artist = Artist.objects.get(name=artist_name)
        except Artist.DoesNotExist:
            # Try case-insensitive search
            try:
                artist = Artist.objects.get(name__iexact=artist_name)
            except Artist.DoesNotExist:
                # Show available artists for better user experience
                artists = Artist.objects.all().order_by('name')
                if artists.exists():
                    artist_names = '\n  '.join([artist.name for artist in artists[:10]])
                    total = artists.count()
                    if total > 10:
                        artist_names += f'\n  ... and {total - 10} more'
                    raise CommandError(
                        f'Artist "{artist_name}" does not exist.\n\n'
                        f'Available artists:\n  {artist_names}\n\n'
                        f'Please use the exact artist name as it appears in the list.'
                    )
                else:
                    raise CommandError(f'Artist "{artist_name}" does not exist. No artists found in database.')
        
        key_name = options['name'] or f'API Key for {artist.name}'
        
        # Create the API key
        api_key = APIKey.objects.create(
            name=key_name,
            artist=artist,
            rate_limit=options['rate_limit']
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created API key for {artist.name}')
        )
        self.stdout.write(f'Key Name: {api_key.name}')
        self.stdout.write(f'API Key: {api_key.key}')
        self.stdout.write(f'Rate Limit: {api_key.rate_limit} requests/hour')
        self.stdout.write('\nIMPORTANT: Save this API key securely. It cannot be retrieved later.')