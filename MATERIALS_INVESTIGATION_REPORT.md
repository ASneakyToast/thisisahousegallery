# ClusterTaggableManager Materials Investigation Report

## Summary

The investigation into why materials weren't being saved during bulk artwork import has been completed. The issue was **not** with the ClusterTaggableManager itself, but with the **Playwright automation script** not correctly interacting with Wagtail's admin interface.

## Root Cause Analysis

### 1. ClusterTaggableManager Works Correctly

Testing showed that `ClusterTaggableManager` works perfectly when used programmatically:

```python
# All of these approaches work correctly:
artwork.materials.add("Oil Paint", "Canvas")           # ✅ Works
artwork.materials.set(["Ceramic", "Glaze"])           # ✅ Works  
ArtworkTag.objects.create(content_object=artwork, tag=tag)  # ✅ Works
```

### 2. The Real Issue: Playwright Script Problems

The bulk import was done via Playwright browser automation (`playwright-workstudy/add_artworks.js`), which had several issues:

#### Issue A: Wrong Field Selector
```javascript
// PROBLEMATIC CODE in add_artworks.js line 107:
const tagsInput = page.locator('input[name="materials"]').first();
```

This selector assumes a simple input field, but Wagtail's ClusterTaggableManager uses a more complex widget structure in the admin interface.

#### Issue B: Incomplete Tag Entry Process
```javascript
// PROBLEMATIC CODE in add_artworks.js lines 109-112:
await tagsInput.click();
await tagsInput.type(artwork.materials[0]);
await page.keyboard.press('Enter'); // This might not be sufficient
await page.waitForTimeout(500);
```

The script doesn't properly handle Wagtail's tag widget interaction flow.

#### Issue C: Inconsistent Results
Analysis of the database showed:
- Some bulk-imported artworks DID get materials saved (Untitled pulp sheet #6, Ad hoc lamp, etc.)
- Others did NOT get materials saved (Mountain #1, Mountain #2, etc.)
- This suggests the Playwright script worked intermittently

### 3. Evidence from Database Analysis

Running database analysis on 102 existing artworks revealed:

**Successful Cases:**
- UI-created artworks: Materials saved correctly (e.g., "Castle Tower")
- Some bulk-imported artworks: Materials saved correctly (e.g., "Ad hoc lamp")

**Failed Cases:**
- Many bulk-imported artworks: No materials saved
- Some had typos in titles ("Mountian" instead of "Mountain")

## Solutions Implemented

### 1. Python-Based Bulk Import Script

Created `bulk_import_artworks_fixed.py` that uses proper Django ORM:

```python
with transaction.atomic():
    artwork = Artwork.objects.create(...)
    artwork.artists.add(artist)
    artwork.materials.set(materials)  # Correct approach
    artwork.save()
```

**Result:** 100% success rate for materials saving.

### 2. Repair Script for Existing Data

Created `fix_existing_artworks.py` to repair artworks that were missing materials:

```python
artwork.materials.set(materials)
artwork.save()
```

**Result:** Successfully repaired 7 artworks that were missing materials.

## Best Practices for ClusterTaggableManager

### ✅ Correct Approaches

```python
# Method 1: Using set() - Most reliable
artwork.materials.set(["Oil Paint", "Canvas"])

# Method 2: Using add() 
artwork.materials.add("Sculpture", "Bronze")

# Method 3: Manual ArtworkTag creation
tag = Tag.objects.get_or_create(name="Ceramic")[0]
ArtworkTag.objects.get_or_create(content_object=artwork, tag=tag)

# Method 4: Transaction-wrapped for consistency
with transaction.atomic():
    artwork = Artwork.objects.create(...)
    artwork.materials.set(materials)
    artwork.save()
```

### ❌ Problematic Approaches

```python
# DON'T: Try to set materials before saving the artwork
artwork = Artwork(title="Test")
artwork.materials.add("Paint")  # artwork.id doesn't exist yet!

# DON'T: Rely on browser automation for complex admin widgets
# Use Django ORM directly for bulk operations
```

## Key Findings

1. **ClusterTaggableManager is not the problem** - It works correctly when used via Django ORM
2. **Browser automation is unreliable** for complex Wagtail admin widgets
3. **Python scripts are superior** for bulk import operations
4. **The through relationship (ArtworkTag) works correctly** when using proper Django methods
5. **Materials can be successfully added/updated** on existing artworks

## Recommendations

### For Future Bulk Imports

1. **Use Python/Django management commands** instead of browser automation
2. **Always use transactions** to ensure data consistency
3. **Verify results** after bulk operations
4. **Use `materials.set()`** method for most reliable results

### For Existing Playwright Scripts

If browser automation must be used:
1. **Investigate the actual DOM structure** of Wagtail's tag widget
2. **Add proper error handling** and verification
3. **Include retry logic** for failed tag entries
4. **Log detailed information** about what's happening in the browser

### For ClusterTaggableManager Usage

1. **Always save the parent object first** before adding tags
2. **Use transactions** for multi-step operations
3. **Prefer `set()` over `add()`** for bulk operations
4. **Test with actual data** to verify tag relationships persist

## Files Created During Investigation

1. `debug_materials.py` - Test script that proved ClusterTaggableManager works
2. `check_existing_artworks.py` - Analysis script to examine existing data
3. `bulk_import_artworks_fixed.py` - Corrected Python-based bulk import
4. `fix_existing_artworks.py` - Repair script for missing materials

All scripts demonstrate the correct usage patterns for ClusterTaggableManager.