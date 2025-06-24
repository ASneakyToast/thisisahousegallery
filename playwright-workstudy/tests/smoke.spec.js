import { test, expect } from '@playwright/test';
import { DataLoader, CMSHelpers, Logger } from '../utils/index.js';
import { Environment } from '../config/environment.js';

test.describe('Smoke Tests', () => {
  test.beforeAll(async () => {
    Logger.info('Starting smoke tests');
    Logger.info('Environment configuration', Environment.getInfo());
  });

  test('environment configuration is valid', async () => {
    expect(() => Environment.validate()).not.toThrow();
    
    const info = Environment.getInfo();
    expect(info.baseUrl).toBeTruthy();
    expect(info.devMode).toBeTruthy();
    
    Logger.success('Environment configuration is valid');
  });

  test('data files are valid and accessible', async () => {
    const validation = await DataLoader.validateData();
    
    expect(validation.valid).toBe(true);
    expect(validation.errors).toHaveLength(0);
    expect(validation.stats.artistCount).toBeGreaterThan(0);
    expect(validation.stats.artworkCount).toBeGreaterThan(0);
    
    Logger.success(`Data validation passed: ${validation.stats.artistCount} artists, ${validation.stats.artworkCount} artworks`);
  });

  test('can load and process data batches', async () => {
    const artists = await DataLoader.getArtistBatch(1, 3);
    expect(artists).toHaveLength(3);
    expect(artists[0]).toHaveProperty('id');
    expect(artists[0]).toHaveProperty('name');
    
    const artworks = await DataLoader.getArtworkBatch(1, 3);
    expect(artworks).toHaveLength(3);
    expect(artworks[0]).toHaveProperty('id');
    expect(artworks[0]).toHaveProperty('title');
    
    Logger.success('Data batch loading works correctly');
  });

  test('can access Wagtail admin interface', async ({ page }) => {
    await CMSHelpers.navigateToAdmin(page);
    
    // Should be on admin dashboard
    await expect(page).toHaveURL(/.*\/admin\/.*/);
    
    // Should see admin interface elements
    await expect(page.locator('.wagtail-logo, .header-logo, h1')).toBeVisible();
    
    Logger.success('Wagtail admin interface is accessible');
  });

  test('can navigate to artists section', async ({ page }) => {
    await CMSHelpers.navigateToAdmin(page, 'snippets/artists/artist/');
    
    // Should be on artists listing page
    await expect(page).toHaveURL(/.*artists.*artist.*/);
    
    Logger.success('Artists section is accessible');
  });

  test('can navigate to artworks section', async ({ page }) => {
    await CMSHelpers.navigateToAdmin(page, 'snippets/artworks/artwork/');
    
    // Should be on artworks listing page  
    await expect(page).toHaveURL(/.*artworks.*artwork.*/);
    
    Logger.success('Artworks section is accessible');
  });

  test('data relationships are valid', async () => {
    const artists = await DataLoader.loadArtists();
    const artworks = await DataLoader.loadArtworks();
    
    // Check that artwork artist references exist
    const artistIds = new Set(artists.map(a => a.id));
    const orphanedArtworks = artworks.filter(artwork => 
      artwork.artist_id && !artistIds.has(artwork.artist_id)
    );
    
    expect(orphanedArtworks).toHaveLength(0);
    
    Logger.success('Data relationships are valid');
  });
});