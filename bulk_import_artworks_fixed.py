#!/usr/bin/env python
"""
Proper bulk import script for artworks using ClusterTaggableManager correctly
"""

import os
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local_offline')
django.setup()

from housegallery.artworks.models import Artwork, ArtworkTag
from housegallery.artists.models import Artist
from taggit.models import Tag
from django.db import transaction

# Artwork data from the original Playwright script
artworks_data = [
    {
        "title": "Mountain #1",  # Fixed typo from "Mountian"
        "date": "2023-01-01",
        "size": "7 1/4 x 7 1/4 x 1 1/2",
        "materials": ["Printmedia"]
    },
    {
        "title": "Mountain #2",  # Fixed typo from "Mountian" 
        "date": "2023-01-01",
        "size": "7 1/4 x 5 1/2 x 1 3/4", 
        "materials": ["Printmedia"]
    },
    # Add other missing materials artworks
    {
        "title": "There's a pea in my bed",
        "date": "2023-01-01",
        "size": "Unknown",
        "materials": ["Mixed Media"]  # Add a reasonable material
    },
    {
        "title": "Theory of adventure",
        "date": "2023-01-01", 
        "size": "Unknown",
        "materials": ["Drawing"]  # Add a reasonable material
    }
]

def bulk_import_artworks():
    """Properly import artworks with materials using ClusterTaggableManager"""
    
    print("=== Bulk Import Artworks (Fixed) ===")
    
    # Get or create Joel Lithgow as artist
    artist, created = Artist.objects.get_or_create(
        name="Joel Lithgow",
        defaults={'bio': 'Artist for bulk import testing'}
    )
    print(f"Artist: {artist} (created: {created})")
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for artwork_data in artworks_data:
        title = artwork_data['title']
        
        try:
            print(f"\n🎨 Processing: {title}")
            
            # Check if artwork already exists
            if Artwork.objects.filter(title=title).exists():
                print(f"⏭️  Artwork already exists, updating materials: {title}")
                artwork = Artwork.objects.get(title=title)
                update_existing = True
            else:
                print(f"✨ Creating new artwork: {title}")
                update_existing = False
            
            # Use transaction to ensure consistency
            with transaction.atomic():
                if not update_existing:
                    # Parse date
                    date_obj = None
                    if artwork_data.get('date'):
                        try:
                            date_obj = datetime.strptime(artwork_data['date'], '%Y-%m-%d').date()
                        except ValueError:
                            print(f"⚠️  Invalid date format: {artwork_data['date']}")
                    
                    # Create artwork
                    artwork = Artwork.objects.create(
                        title=title,
                        description=f"Bulk imported artwork: {title}",
                        size=artwork_data.get('size', ''),
                        date=date_obj
                    )
                    
                    # Add artist relationship
                    artwork.artists.add(artist)
                    print(f"  ✅ Created artwork with artist")
                
                # Add materials using the correct ClusterTaggableManager approach
                materials = artwork_data.get('materials', [])
                if materials:
                    # Clear existing materials (for updates)
                    if update_existing:
                        artwork.materials.clear()
                    
                    # Add new materials - using set() method which is most reliable
                    artwork.materials.set(materials)
                    print(f"  ✅ Set materials: {materials}")
                
                # Save the artwork
                artwork.save()
                print(f"  ✅ Saved artwork")
            
            # Verify materials were saved
            artwork.refresh_from_db()
            saved_materials = list(artwork.materials.all())
            print(f"  🔍 Verified materials: {[m.name for m in saved_materials]}")
            
            if saved_materials:
                success_count += 1
                print(f"  ✅ SUCCESS: Materials saved correctly")
            else:
                error_count += 1
                print(f"  ❌ ERROR: Materials not saved!")
                
        except Exception as e:
            error_count += 1
            print(f"  ❌ ERROR processing {title}: {e}")
    
    print(f"\n🎉 Bulk import complete!")
    print(f"✅ Success: {success_count}")
    print(f"⏭️  Skipped: {skip_count}")
    print(f"❌ Errors: {error_count}")
    
    # Final verification
    print(f"\n=== Final Verification ===")
    for artwork_data in artworks_data:
        title = artwork_data['title']
        try:
            artwork = Artwork.objects.get(title=title)
            materials = list(artwork.materials.all())
            artwork_tags = ArtworkTag.objects.filter(content_object=artwork)
            
            print(f"{title}:")
            print(f"  Materials: {[m.name for m in materials]}")
            print(f"  ArtworkTag count: {artwork_tags.count()}")
            
            if not materials:
                print(f"  ⚠️  NO MATERIALS!")
        except Artwork.DoesNotExist:
            print(f"{title}: NOT FOUND")

if __name__ == "__main__":
    bulk_import_artworks()