import { expect } from '@playwright/test';
import { Environment } from '../config/environment.js';

/**
 * CMS Helper utilities for Wagtail admin interactions
 */
export class CMSHelpers {
  
  /**
   * Navigate to a specific admin section
   * @param {Page} page - Playwright page object
   * @param {string} section - Admin section path (e.g., 'artists/artist/', 'artworks/artwork/')
   */
  static async navigateToAdmin(page, section = '') {
    const url = Environment.getAdminUrl(section);
    await page.goto(url, { waitUntil: 'networkidle' });
    
    // Wait for admin interface to load
    await page.waitForSelector('.wagtail-logo, .header-logo, h1', { timeout: 10000 });
  }

  /**
   * Check if an artist exists in the CMS
   * @param {Page} page - Playwright page object
   * @param {string} artistName - Name of the artist to search for
   * @returns {boolean} True if artist exists, false otherwise
   */
  static async checkArtistExists(page, artistName) {
    try {
      await this.navigateToAdmin(page, 'snippets/artists/artist/');
      
      // Look for search form
      const searchInput = page.locator('input[name="q"], input[type="search"], .search-input input');
      if (await searchInput.count() > 0) {
        await searchInput.first().fill(artistName);
        
        // Submit search
        const searchButton = page.locator('button[type="submit"], .button-search, input[type="submit"]');
        if (await searchButton.count() > 0) {
          await searchButton.first().click();
          await page.waitForLoadState('networkidle');
        }
      }
      
      // Check results
      const resultsTable = page.locator('.listing tbody tr, .results .result');
      const count = await resultsTable.count();
      
      if (count > 0) {
        // Check if any result matches exactly
        for (let i = 0; i < count; i++) {
          const row = resultsTable.nth(i);
          const text = await row.textContent();
          if (text && text.toLowerCase().includes(artistName.toLowerCase())) {
            return true;
          }
        }
      }
      
      return false;
    } catch (error) {
      console.warn(`Error checking artist existence: ${error.message}`);
      return false;
    }
  }

  /**
   * Check if an artwork exists in the CMS
   * @param {Page} page - Playwright page object
   * @param {string} artworkTitle - Title of the artwork to search for
   * @returns {boolean} True if artwork exists, false otherwise
   */
  static async checkArtworkExists(page, artworkTitle) {
    try {
      await this.navigateToAdmin(page, 'snippets/artworks/artwork/');
      
      // Look for search form
      const searchInput = page.locator('input[name="q"], input[type="search"], .search-input input');
      if (await searchInput.count() > 0) {
        await searchInput.first().fill(artworkTitle);
        
        // Submit search
        const searchButton = page.locator('button[type="submit"], .button-search, input[type="submit"]');
        if (await searchButton.count() > 0) {
          await searchButton.first().click();
          await page.waitForLoadState('networkidle');
        }
      }
      
      // Check results
      const resultsTable = page.locator('.listing tbody tr, .results .result');
      const count = await resultsTable.count();
      
      if (count > 0) {
        // Check if any result matches exactly
        for (let i = 0; i < count; i++) {
          const row = resultsTable.nth(i);
          const text = await row.textContent();
          if (text && text.toLowerCase().includes(artworkTitle.toLowerCase())) {
            return true;
          }
        }
      }
      
      return false;
    } catch (error) {
      console.warn(`Error checking artwork existence: ${error.message}`);
      return false;
    }
  }

  /**
   * Create a new artist in the CMS
   * @param {Page} page - Playwright page object
   * @param {Object} artistData - Artist data object
   */
  static async createArtist(page, artistData) {
    try {
      // Navigate to add artist page
      await this.navigateToAdmin(page, 'snippets/artists/artist/add/');
      
      // Wait for form to load
      await page.waitForSelector('form', { timeout: 10000 });
      
      // Fill basic fields
      await this.fillField(page, 'name', artistData.name);
      
      if (artistData.bio) {
        await this.fillField(page, 'bio', artistData.bio);
      }
      
      if (artistData.website) {
        await this.fillField(page, 'website', artistData.website);
      }
      
      if (artistData.birth_year) {
        await this.fillField(page, 'birth_year', artistData.birth_year.toString());
      }
      
      // Handle social media links if present
      if (artistData.social_media_links && artistData.social_media_links.length > 0) {
        await this.handleSocialMediaLinks(page, artistData.social_media_links);
      }
      
      // Save the artist
      await this.saveForm(page);
      
      // Verify success
      await this.verifySuccess(page);
      
    } catch (error) {
      throw new Error(`Failed to create artist "${artistData.name}": ${error.message}`);
    }
  }

  /**
   * Create a new artwork in the CMS
   * @param {Page} page - Playwright page object
   * @param {Object} artworkData - Artwork data object
   * @param {Object} artistData - Associated artist data (for reference)
   */
  static async createArtwork(page, artworkData, artistData) {
    try {
      // Navigate to add artwork page
      await this.navigateToAdmin(page, 'snippets/artworks/artwork/add/');
      
      // Wait for form to load
      await page.waitForSelector('form', { timeout: 10000 });
      
      // Fill basic fields
      await this.fillField(page, 'title', artworkData.title);
      
      if (artworkData.description) {
        await this.fillField(page, 'description', artworkData.description);
      }
      
      if (artworkData.size) {
        await this.fillField(page, 'size', artworkData.size);
      }
      
      // Handle artist selection
      if (artistData) {
        await this.selectArtist(page, artistData.name);
      }
      
      // Handle date field
      if (artworkData.date) {
        await this.handleDateField(page, artworkData.date);
      }
      
      // Handle materials (tags)
      if (artworkData.materials && artworkData.materials.length > 0) {
        await this.handleMaterialTags(page, artworkData.materials);
      }
      
      // Handle artifacts (StreamField)
      if (artworkData.artifacts && artworkData.artifacts.length > 0) {
        await this.handleArtifacts(page, artworkData.artifacts);
      }
      
      // Save the artwork
      await this.saveForm(page);
      
      // Verify success
      await this.verifySuccess(page);
      
    } catch (error) {
      throw new Error(`Failed to create artwork "${artworkData.title}": ${error.message}`);
    }
  }

  /**
   * Fill a form field with multiple selector attempts
   * @param {Page} page - Playwright page object
   * @param {string} fieldName - Name of the field
   * @param {string} value - Value to fill
   */
  static async fillField(page, fieldName, value) {
    const selectors = [
      `input[name="${fieldName}"]`,
      `textarea[name="${fieldName}"]`,
      `select[name="${fieldName}"]`,
      `#id_${fieldName}`,
      `[name="${fieldName}"]`
    ];
    
    for (const selector of selectors) {
      const field = page.locator(selector);
      if (await field.count() > 0) {
        await field.first().fill(value);
        return;
      }
    }
    
    console.warn(`Could not find field: ${fieldName}`);
  }

  /**
   * Handle artist selection in artwork form
   * @param {Page} page - Playwright page object
   * @param {string} artistName - Name of the artist to select
   */
  static async selectArtist(page, artistName) {
    try {
      // Try different possible artist field implementations
      const artistSelectors = [
        'select[name="artist"]',
        'input[name="artist"]',
        '#id_artist',
        '.artist-chooser input',
        '.chooser input'
      ];
      
      for (const selector of artistSelectors) {
        const field = page.locator(selector);
        if (await field.count() > 0) {
          const fieldType = await field.getAttribute('type');
          
          if (fieldType === 'hidden' || await field.locator('..').locator('.chooser').count() > 0) {
            // This is likely a chooser widget
            const chooserButton = page.locator('.chooser .action-choose, .action-choose');
            if (await chooserButton.count() > 0) {
              await chooserButton.click();
              
              // Handle modal or popup
              await page.waitForSelector('.modal-content, .chooser-modal', { timeout: 5000 });
              
              // Search for artist
              const searchInput = page.locator('.modal input[type="search"], .chooser-modal input[type="search"]');
              if (await searchInput.count() > 0) {
                await searchInput.fill(artistName);
                await page.keyboard.press('Enter');
                await page.waitForTimeout(1000);
              }
              
              // Select the artist
              const artistLink = page.locator(`text="${artistName}"`).first();
              await artistLink.click();
              return;
            }
          } else {
            // Regular input or select field
            await field.fill(artistName);
            
            // If it's an autocomplete, wait for suggestions and click
            await page.waitForTimeout(500);
            const suggestion = page.locator(`text="${artistName}"`).first();
            if (await suggestion.count() > 0) {
              await suggestion.click();
            }
            return;
          }
        }
      }
      
      console.warn(`Could not find artist selection field`);
    } catch (error) {
      console.warn(`Error selecting artist: ${error.message}`);
    }
  }

  /**
   * Handle date field input
   * @param {Page} page - Playwright page object
   * @param {string} dateString - ISO date string
   */
  static async handleDateField(page, dateString) {
    try {
      const date = new Date(dateString);
      const dateFormatted = date.toISOString().split('T')[0]; // YYYY-MM-DD format
      
      const dateSelectors = [
        'input[name="date"]',
        '#id_date',
        'input[type="date"]',
        'input[type="datetime-local"]'
      ];
      
      for (const selector of dateSelectors) {
        const field = page.locator(selector);
        if (await field.count() > 0) {
          await field.fill(dateFormatted);
          return;
        }
      }
      
      console.warn(`Could not find date field`);
    } catch (error) {
      console.warn(`Error handling date field: ${error.message}`);
    }
  }

  /**
   * Handle material tags
   * @param {Page} page - Playwright page object
   * @param {Array} materials - Array of material strings
   */
  static async handleMaterialTags(page, materials) {
    try {
      const tagSelectors = [
        'input[name="materials"]',
        '#id_materials',
        '.tagit input',
        '.tag-field input'
      ];
      
      for (const selector of tagSelectors) {
        const field = page.locator(selector);
        if (await field.count() > 0) {
          const tagString = materials.join(', ');
          await field.fill(tagString);
          return;
        }
      }
      
      console.warn(`Could not find materials field`);
    } catch (error) {
      console.warn(`Error handling materials: ${error.message}`);
    }
  }

  /**
   * Handle social media links StreamField
   * @param {Page} page - Playwright page object
   * @param {Array} socialLinks - Array of social media link objects
   */
  static async handleSocialMediaLinks(page, socialLinks) {
    try {
      // This is a complex StreamField implementation
      // For now, we'll skip this in the basic implementation
      console.log(`Skipping social media links (${socialLinks.length} links) - complex StreamField`);
    } catch (error) {
      console.warn(`Error handling social media links: ${error.message}`);
    }
  }

  /**
   * Handle artifacts StreamField
   * @param {Page} page - Playwright page object
   * @param {Array} artifacts - Array of artifact objects
   */
  static async handleArtifacts(page, artifacts) {
    try {
      // This is a complex StreamField implementation
      // For now, we'll skip this in the basic implementation
      console.log(`Skipping artifacts (${artifacts.length} items) - complex StreamField`);
    } catch (error) {
      console.warn(`Error handling artifacts: ${error.message}`);
    }
  }

  /**
   * Save the form
   * @param {Page} page - Playwright page object
   */
  static async saveForm(page) {
    const saveSelectors = [
      'button[name="_save"]',
      'input[name="_save"]',
      'button[type="submit"]',
      '.button-save',
      '.action-save'
    ];
    
    for (const selector of saveSelectors) {
      const button = page.locator(selector);
      if (await button.count() > 0) {
        await button.click();
        await page.waitForLoadState('networkidle');
        return;
      }
    }
    
    throw new Error('Could not find save button');
  }

  /**
   * Verify successful form submission
   * @param {Page} page - Playwright page object
   */
  static async verifySuccess(page) {
    try {
      // Wait for success message or redirect
      await page.waitForSelector(
        '.success, .messages .success, .message-success',
        { timeout: 10000 }
      );
    } catch (error) {
      // If no success message, check if we're back on the listing page
      const currentUrl = page.url();
      if (currentUrl.includes('/add/')) {
        throw new Error('Form submission may have failed - still on add page');
      }
    }
  }

  /**
   * Ensure an artist exists (create if missing)
   * @param {Page} page - Playwright page object
   * @param {Object} artistData - Artist data object
   * @returns {boolean} True if artist exists or was created
   */
  static async ensureArtistExists(page, artistData) {
    try {
      const exists = await this.checkArtistExists(page, artistData.name);
      
      if (!exists) {
        console.log(`🎨 Creating missing artist: ${artistData.name}`);
        await this.createArtist(page, artistData);
        return true;
      }
      
      console.log(`✅ Artist already exists: ${artistData.name}`);
      return true;
    } catch (error) {
      throw new Error(`Failed to ensure artist exists: ${error.message}`);
    }
  }

  /**
   * Retry wrapper for operations that might fail
   * @param {Function} operation - Function to retry
   * @param {number} maxRetries - Maximum number of retries
   * @param {number} delay - Delay between retries in milliseconds
   */
  static async withRetry(operation, maxRetries = Environment.batch.maxRetries, delay = Environment.batch.retryDelay) {
    let lastError;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error;
        console.warn(`⚠️  Attempt ${attempt}/${maxRetries} failed: ${error.message}`);
        
        if (attempt < maxRetries) {
          const backoffDelay = delay * Math.pow(2, attempt - 1); // Exponential backoff
          console.log(`⏳ Waiting ${backoffDelay}ms before retry...`);
          await new Promise(resolve => setTimeout(resolve, backoffDelay));
        }
      }
    }
    
    throw new Error(`Operation failed after ${maxRetries} attempts: ${lastError.message}`);
  }
}