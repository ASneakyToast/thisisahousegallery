#!/usr/bin/env python
"""
Fix existing artworks that don't have materials saved
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local_offline')
django.setup()

from housegallery.artworks.models import Artwork, ArtworkTag
from taggit.models import Tag
from django.db import transaction

def fix_existing_artworks():
    """Fix existing artworks that are missing materials"""
    
    print("=== Fix Existing Artworks ===")
    
    # Known artworks that should have materials but don't
    fixes = [
        {
            "title": "Mountian #1",  # The typo version
            "materials": ["Printmedia"]
        },
        {
            "title": "Mountian #2",  # The typo version  
            "materials": ["Printmedia"]
        },
        {
            "title": "There's a pea in my bed",
            "materials": ["Mixed Media"]
        },
        {
            "title": "Theory of adventure", 
            "materials": ["Drawing"]
        },
        {
            "title": "Keep going",
            "materials": ["Drawing"]
        },
        {
            "title": "self portrait",
            "materials": ["Drawing"]
        },
        {
            "title": "untitled",
            "materials": ["Painting"]
        },
        {
            "title": "See thru Thursday",
            "materials": ["Mixed Media"]
        },
        {
            "title": "Toe",
            "materials": ["Sculpture"]
        },
        {
            "title": "Refurbished scraps",
            "materials": ["Mixed Media"]
        },
        {
            "title": "Collaborative Living",
            "materials": ["Installation"]
        }
    ]
    
    fixed_count = 0
    not_found_count = 0
    
    for fix in fixes:
        title = fix['title']
        materials = fix['materials']
        
        try:
            # Find artwork by title (case-insensitive)
            artwork = Artwork.objects.filter(title__iexact=title).first()
            
            if not artwork:
                print(f"❌ Artwork not found: {title}")
                not_found_count += 1
                continue
            
            # Check current materials
            current_materials = list(artwork.materials.all())
            
            if current_materials:
                print(f"⏭️  Artwork already has materials: {title} - {[m.name for m in current_materials]}")
                continue
            
            print(f"🔧 Fixing: {title}")
            
            with transaction.atomic():
                # Set materials
                artwork.materials.set(materials)
                artwork.save()
                
                # Verify
                artwork.refresh_from_db()
                saved_materials = list(artwork.materials.all())
                
                if saved_materials:
                    print(f"  ✅ SUCCESS: Added materials {[m.name for m in saved_materials]}")
                    fixed_count += 1
                else:
                    print(f"  ❌ FAILED: Materials not saved")
                    
        except Exception as e:
            print(f"❌ Error fixing {title}: {e}")
    
    print(f"\n🎉 Fix complete!")
    print(f"✅ Fixed: {fixed_count}")
    print(f"❌ Not found: {not_found_count}")

if __name__ == "__main__":
    fix_existing_artworks()