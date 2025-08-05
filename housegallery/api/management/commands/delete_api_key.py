from django.core.management.base import BaseCommand, CommandError
from housegallery.api.models import APIKey


class Command(BaseCommand):
    help = 'Delete an API key by key value or name'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--key',
            type=str,
            help='The API key value to delete'
        )
        parser.add_argument(
            '--name',
            type=str,
            help='The name of the API key to delete'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt'
        )
    
    def handle(self, *args, **options):
        if not options['key'] and not options['name']:
            raise CommandError('You must provide either --key or --name')
        
        if options['key'] and options['name']:
            raise CommandError('Please provide either --key or --name, not both')
        
        try:
            if options['key']:
                api_key = APIKey.objects.get(key=options['key'])
            else:
                api_key = APIKey.objects.get(name=options['name'])
        except APIKey.DoesNotExist:
            identifier = options['key'] or options['name']
            raise CommandError(f'API key "{identifier}" not found')
        
        # Show API key details
        self.stdout.write(f'\nAPI Key Details:')
        self.stdout.write(f'  Name: {api_key.name}')
        self.stdout.write(f'  Artist: {api_key.artist.name if api_key.artist else "None"}')
        self.stdout.write(f'  Created: {api_key.created}')
        self.stdout.write(f'  Last Used: {api_key.last_used or "Never"}')
        self.stdout.write(f'  Active: {api_key.is_active}')
        
        # Confirm deletion unless --force is used
        if not options['force']:
            confirm = input('\nAre you sure you want to delete this API key? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Deletion cancelled'))
                return
        
        # Delete the API key
        key_name = api_key.name
        api_key.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully deleted API key: {key_name}')
        )