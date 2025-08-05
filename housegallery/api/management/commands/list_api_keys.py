from django.core.management.base import BaseCommand
from django.utils import timezone
from housegallery.api.models import APIKey


class Command(BaseCommand):
    help = 'List all API keys'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--artist',
            type=str,
            help='Filter by artist name'
        )
        parser.add_argument(
            '--active',
            action='store_true',
            help='Show only active keys'
        )
        parser.add_argument(
            '--inactive',
            action='store_true',
            help='Show only inactive keys'
        )
        parser.add_argument(
            '--show-keys',
            action='store_true',
            help='Show the actual API key values (use with caution)'
        )
    
    def handle(self, *args, **options):
        # Build query
        queryset = APIKey.objects.all()
        
        if options['artist']:
            queryset = queryset.filter(artist__name__icontains=options['artist'])
        
        if options['active']:
            queryset = queryset.filter(is_active=True)
        elif options['inactive']:
            queryset = queryset.filter(is_active=False)
        
        # Order by creation date
        queryset = queryset.order_by('-created_at')
        
        if not queryset.exists():
            self.stdout.write(self.style.WARNING('No API keys found'))
            return
        
        # Display header
        self.stdout.write('\nAPI Keys:')
        self.stdout.write('-' * 80)
        
        for api_key in queryset:
            self.stdout.write(f'\nName: {api_key.name}')
            if options['show_keys']:
                self.stdout.write(f'Key: {api_key.key}')
            else:
                # Show masked key (first 8 chars only)
                masked_key = api_key.key[:8] + '...' if len(api_key.key) > 8 else api_key.key
                self.stdout.write(f'Key: {masked_key} (use --show-keys to see full key)')
            
            self.stdout.write(f'Artist: {api_key.artist.name if api_key.artist else "None"}')
            self.stdout.write(f'Active: {"Yes" if api_key.is_active else "No"}')
            self.stdout.write(f'Rate Limit: {api_key.rate_limit} requests/hour')
            self.stdout.write(f'Created: {api_key.created_at.strftime("%Y-%m-%d %H:%M:%S")}')
            
            if api_key.last_used:
                self.stdout.write(f'Last Used: {api_key.last_used.strftime("%Y-%m-%d %H:%M:%S")}')
            else:
                self.stdout.write(f'Last Used: Never')
            
            self.stdout.write('-' * 80)
        
        self.stdout.write(f'\nTotal: {queryset.count()} API key(s)')