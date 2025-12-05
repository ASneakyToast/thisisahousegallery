# Performance Optimization Release

**Date:** December 5, 2025
**Branch:** `feature/art-admin-upgrades`
**Commits:** `fc068ef`, `0ed476f`

## Summary

Major performance optimization for exhibition pages, reducing page load times from 6+ seconds to ~1.2 seconds on cached requests.

## Problem

The site was experiencing slow page loads, particularly on exhibition pages with many images. Root causes identified:

1. **N+1 Query Issues** - Exhibition detail pages were making 60+ database queries due to unoptimized relationship traversal
2. **Cross-Region Cache Latency** - Production cache (DatabaseCache) required querying Cloud SQL (us-west2) from Cloud Run (us-west1), adding ~150ms per cache operation
3. **Redundant Queries** - Multiple `.exists()`, `.count()`, `.first()` calls on the same querysets

## Changes

### 1. Exhibition Query Optimization

**File:** `housegallery/exhibitions/models.py`

#### New: `get_optimized_exhibition_detail()` Class Method
A new class method that loads an ExhibitionPage with all relationships optimally prefetched in ~8 queries instead of 60+:
- Exhibition artists
- Artworks with images, artists, and materials
- All photo types (installation, opening, showcard, in-progress) with renditions

#### New: `get_context()` on ExhibitionPage
Automatically applies prefetched data when serving exhibition detail pages, ensuring templates use the optimized queryset.

#### Refactored: `get_unified_gallery_images()`
- Now uses `list()` to access prefetched data instead of re-querying
- Checks prefetched renditions before calling `get_rendition()`
- Reduced from ~60 queries to using prefetched data

#### Refactored: `get_all_gallery_images()` and `get_filtered_gallery_images()`
- Added helper functions to check prefetched renditions first
- Falls back to `get_rendition()` only if not in prefetch cache
- Uses original file URL for full-size images instead of generating renditions

#### Fixed: `get_related_showcard_images()`
- Changed from multiple queries (`.exists()`, `.count()`, `.first()`, `.last()`) to single fetch with Python slicing

### 2. Enhanced Rendition Management

**File:** `housegallery/images/management/commands/generate_renditions.py`

Added new options:
- `--dry-run` - Preview what would be generated without executing
- `--missing-only` - Only process images missing standard renditions (fast incremental)
- `--image-id <id>` - Generate renditions for a specific image
- `--batch-size <n>` - Control progress reporting frequency

### 3. Production Cache Optimization

**File:** `config/settings/production.py`

Switched from DatabaseCache to LocMemCache:
- **Before:** Every cache read/write required cross-region database query (~150ms latency)
- **After:** Cache lives in container memory (sub-millisecond access)

Trade-offs:
- Cache clears on container restart
- First request after restart is slower (cache cold)
- Subsequent requests are fast

Sessions moved to database backend for persistence across restarts.

## Performance Results

### Exhibition Detail Page (`/exhibitions/your-least-favorite-work/`)

| Metric | Before | After |
|--------|--------|-------|
| Database Queries | ~60+ | 28 |
| Duplicate Queries | Many | 0 |
| Cold Cache Load | 6.5s | 5.6s |
| Warm Cache Load | 6.5s | **1.2s** |

### Exhibition Listing Page (`/exhibitions/`)

| Metric | Before | After |
|--------|--------|-------|
| Database Queries | ~100+ | 31 |
| Duplicate Queries | Many | 0 |
| Load Time | ~6s | ~2s |

## Pre-existing Infrastructure

These features were already in place and continue to work:

### Automatic Rendition Generation (Signal)
**File:** `housegallery/images/models.py:357-383`

When any `CustomImage` is created, standard renditions are automatically generated:
- `width-400` (thumbnail)
- `width-400|format-webp`
- `width-1200` (full)
- `width-1200|format-webp`

### Manual Rendition Generation (Command)
```bash
# Check what needs generating
python manage.py generate_renditions --dry-run

# Process only images missing renditions
python manage.py generate_renditions --missing-only

# Process all images
python manage.py generate_renditions
```

## Deployment

Deployed to QA via tag: `dev-perf-optimization`, `dev-cache-fix`

## Future Considerations

1. **CDN Caching** - Could add Cloudflare or similar for edge caching of static pages
2. **Cloud Run Region** - If custom domains now support us-west2, moving Cloud Run would eliminate cross-region latency entirely
3. **Redis/Memorystore** - For higher traffic, a shared in-memory cache would provide faster performance with persistence
