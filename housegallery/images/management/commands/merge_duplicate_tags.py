from django.core.management.base import BaseCommand
from django.db import transaction
from collections import defaultdict
from taggit.models import Tag, TaggedItem


class Command(BaseCommand):
    help = 'Merge duplicate tags that differ only in case (e.g., "Nature" and "nature")'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be merged without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        # Find duplicate tags (case-insensitive)
        duplicates = self.find_duplicate_tags()
        
        if not duplicates:
            self.stdout.write(self.style.SUCCESS('No duplicate tags found.'))
            return

        self.stdout.write(f'Found {len(duplicates)} groups of duplicate tags:')
        
        merge_actions = []
        for canonical_name, duplicate_tags in duplicates.items():
            self.stdout.write(f'\n  Group: "{canonical_name}"')
            
            # Show all variants
            for tag in duplicate_tags:
                usage_count = TaggedItem.objects.filter(tag=tag).count()
                self.stdout.write(f'    - "{tag.name}" (used {usage_count} times)')
            
            # Determine canonical tag (most used, or first alphabetically)
            canonical_tag = self.get_canonical_tag(duplicate_tags)
            tags_to_merge = [tag for tag in duplicate_tags if tag != canonical_tag]
            
            if tags_to_merge:
                merge_actions.append((canonical_tag, tags_to_merge))
                self.stdout.write(f'    → Will merge into: "{canonical_tag.name}"')

        if not merge_actions:
            self.stdout.write(self.style.SUCCESS('No merging needed.'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDry run - no changes made.'))
            return

        # Confirm before proceeding
        if not force:
            confirm = input(f'\nProceed with merging {len(merge_actions)} groups of tags? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write('Cancelled.')
                return

        # Perform the merges
        merged_count = 0
        with transaction.atomic():
            for canonical_tag, tags_to_merge in merge_actions:
                merged_count += self.merge_tags(canonical_tag, tags_to_merge)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully merged {merged_count} duplicate tags.')
        )

    def find_duplicate_tags(self):
        """Find groups of tags that are duplicates when compared case-insensitively."""
        tags = Tag.objects.all()
        groups = defaultdict(list)
        
        for tag in tags:
            groups[tag.name.lower()].append(tag)
        
        # Only return groups with more than one tag
        return {name: tag_list for name, tag_list in groups.items() if len(tag_list) > 1}

    def get_canonical_tag(self, duplicate_tags):
        """
        Determine which tag should be the canonical one.
        Prefers the most-used tag, falling back to alphabetical order.
        """
        # Count usage for each tag
        tag_usage = []
        for tag in duplicate_tags:
            usage_count = TaggedItem.objects.filter(tag=tag).count()
            tag_usage.append((tag, usage_count))
        
        # Sort by usage count (descending), then by name (ascending)
        tag_usage.sort(key=lambda x: (-x[1], x[0].name))
        
        return tag_usage[0][0]

    def merge_tags(self, canonical_tag, tags_to_merge):
        """
        Merge duplicate tags into the canonical tag.
        Returns the number of tags merged.
        """
        merged_count = 0
        
        for tag_to_merge in tags_to_merge:
            # Move all tagged items to the canonical tag
            tagged_items = TaggedItem.objects.filter(tag=tag_to_merge)
            
            for tagged_item in tagged_items:
                # Check if this object already has the canonical tag
                existing = TaggedItem.objects.filter(
                    tag=canonical_tag,
                    content_type=tagged_item.content_type,
                    object_id=tagged_item.object_id
                ).exists()
                
                if not existing:
                    # Move the tagged item to the canonical tag
                    tagged_item.tag = canonical_tag
                    tagged_item.save()
                else:
                    # Delete the duplicate tagged item
                    tagged_item.delete()
            
            # Delete the now-unused tag
            tag_name = tag_to_merge.name
            tag_to_merge.delete()
            merged_count += 1
            
            self.stdout.write(f'  Merged "{tag_name}" into "{canonical_tag.name}"')
        
        return merged_count