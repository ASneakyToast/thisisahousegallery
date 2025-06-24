import { expect } from '@playwright/test';
import { Environment } from '../../config/environment.js';
import { CMSHelpers } from '../../utils/cms-helpers.js';
import { 
  compareArtistData, 
  generateChangeSummary, 
  validateArtistData, 
  extractCMSArtistData,
  isSameArtist 
} from './artist-comparison.js';

/**
 * Enhanced Artist Operations for CMS Management
 * 
 * Provides comprehensive artist CRUD operations with comparison,
 * search, and update capabilities.
 */
export class ArtistOperations {
  
  constructor(page) {
    this.page = page;
  }

  /**
   * Search for an artist by name with enhanced matching
   * @param {string} artistName - Name of the artist to search for
   * @returns {Object} Search result with artist data if found
   */
  async searchArtist(artistName) {
    try {
      console.log(`🔍 Searching for artist: ${artistName}`);
      await CMSHelpers.navigateToAdmin(this.page, 'snippets/artists/artist/');
      
      // Debug: Check what page we're actually on
      const currentUrl = this.page.url();
      const pageTitle = await this.page.title();
      console.log(`📍 Search page URL: ${currentUrl}`);
      console.log(`📍 Search page title: ${pageTitle}`);
      
      // Check if we're on the login page
      if (currentUrl.includes('/login/') || pageTitle.includes('Sign in')) {
        console.error(`❌ Still on login page during search! URL: ${currentUrl}, Title: ${pageTitle}`);
        throw new Error('Authentication failed during search - redirected to login page');
      }
      
      // Get all artists from the listing page
      const artists = await this.getAllArtistsFromListing();
      
      // Try to find exact match first
      const exactMatch = artists.find(artist => 
        artist.name.toLowerCase() === artistName.toLowerCase()
      );
      
      if (exactMatch) {
        return {
          found: true,
          artist: exactMatch,
          matchType: 'exact'
        };
      }
      
      // Try fuzzy matching
      const fuzzyMatch = artists.find(artist => 
        this.calculateSimilarity(artist.name.toLowerCase(), artistName.toLowerCase()) > 0.8
      );
      
      if (fuzzyMatch) {
        return {
          found: true,
          artist: fuzzyMatch,
          matchType: 'fuzzy'
        };
      }
      
      return {
        found: false,
        artist: null,
        matchType: null
      };
      
    } catch (error) {
      console.warn(`Error searching for artist "${artistName}": ${error.message}`);
      return {
        found: false,
        artist: null,
        matchType: null,
        error: error.message
      };
    }
  }

  /**
   * Get all artists from the listing page
   * @returns {Array} Array of artist objects with name and edit URL
   */
  async getAllArtistsFromListing() {
    const artists = [];
    
    try {
      // Wait for the table to load - try multiple selectors
      const tableSelectors = [
        'table tbody tr',
        '.listing tbody tr', 
        'table tr',
        '[role="table"] tr',
        'tbody tr'
      ];
      
      let rows = null;
      for (const selector of tableSelectors) {
        try {
          await this.page.waitForSelector(selector, { timeout: 5000 });
          rows = this.page.locator(selector);
          const count = await rows.count();
          if (count > 0) {
            console.log(`✅ Found ${count} rows using selector: ${selector}`);
            break;
          }
        } catch (error) {
          console.log(`❌ Selector failed: ${selector}`);
          continue;
        }
      }
      
      if (!rows) {
        console.warn('❌ Could not find any table rows with any selector');
        return [];
      }
      
      const rowCount = await rows.count();
      
      for (let i = 0; i < rowCount; i++) {
        const row = rows.nth(i);
        
        // Extract artist name and edit link
        const nameLink = row.locator('a[href*="/edit/"]');
        
        if (await nameLink.count() > 0) {
          const name = await nameLink.textContent();
          const editUrl = await nameLink.getAttribute('href');
          const artistId = this.extractArtistIdFromUrl(editUrl);
          
          artists.push({
            name: name.trim(),
            editUrl,
            id: artistId
          });
        }
      }
      
      return artists;
    } catch (error) {
      console.warn(`Error getting artists from listing: ${error.message}`);
      return [];
    }
  }

  /**
   * Get detailed artist data by navigating to edit form
   * @param {Object} artistSummary - Artist summary from listing
   * @returns {Object} Detailed artist data
   */
  async getArtistData(artistSummary) {
    try {
      // Navigate to the edit page
      const editUrl = Environment.wagtail.baseUrl + artistSummary.editUrl;
      await this.page.goto(editUrl, { waitUntil: 'networkidle' });
      
      // Wait for form to load
      await this.page.waitForSelector('form', { timeout: 10000 });
      
      // Extract all form data
      const artistData = await extractCMSArtistData(this.page);
      
      return {
        ...artistData,
        id: artistSummary.id,
        editUrl: artistSummary.editUrl
      };
      
    } catch (error) {
      console.warn(`Error getting artist data: ${error.message}`);
      return null;
    }
  }

  /**
   * Create a new artist with enhanced form handling
   * @param {Object} artistData - Artist data from test configuration
   * @returns {Object} Creation result
   */
  async createArtist(artistData) {
    try {
      console.log(`🎨 Creating new artist: ${artistData.name}`);
      
      // Validate data first
      const validation = validateArtistData(artistData);
      if (!validation.isValid) {
        throw new Error(`Invalid artist data: ${validation.errors.join(', ')}`);
      }
      
      // Navigate to add page
      console.log(`📍 Navigating to artist add page...`);
      await CMSHelpers.navigateToAdmin(this.page, 'snippets/artists/artist/add/');
      
      // Debug: Check what page we're actually on
      const currentUrl = this.page.url();
      const pageTitle = await this.page.title();
      console.log(`📍 Current URL: ${currentUrl}`);
      console.log(`📍 Page title: ${pageTitle}`);
      
      // Check if we're on the login page
      if (currentUrl.includes('/login/') || pageTitle.includes('Sign in')) {
        console.error(`❌ Still on login page! URL: ${currentUrl}, Title: ${pageTitle}`);
        throw new Error('Authentication failed - redirected to login page');
      }
      
      // Wait for form
      console.log(`⏳ Waiting for form to load...`);
      await this.page.waitForSelector('form', { timeout: 10000 });
      console.log(`✅ Form found and loaded`);
      
      // Additional wait for form to be fully interactive
      await this.page.waitForTimeout(1000);
      
      // Debug: Take snapshot of the form
      console.log(`📸 Taking snapshot of artist form page`);
      await this.page.screenshot({ path: `./test-results/debug-artist-form-${Date.now()}.png`, fullPage: true });
      
      // Fill form fields
      console.log(`📝 Filling form fields for: ${artistData.name}`);
      await this.fillArtistForm(artistData);
      
      // Debug: Take snapshot after filling form
      console.log(`📸 Taking snapshot after filling form`);
      await this.page.screenshot({ path: `./test-results/debug-form-filled-${Date.now()}.png`, fullPage: true });
      
      // Save
      console.log(`💾 Attempting to save artist form`);
      await this.saveArtistForm();
      
      // Debug: Take snapshot after save attempt
      console.log(`📸 Taking snapshot after save attempt`);
      await this.page.screenshot({ path: `./test-results/debug-after-save-${Date.now()}.png`, fullPage: true });
      
      // Check URL after save
      const postSaveUrl = this.page.url();
      const postSaveTitle = await this.page.title();
      console.log(`📍 After save URL: ${postSaveUrl}`);
      console.log(`📍 After save title: ${postSaveTitle}`);
      
      // Verify success
      await this.verifyArtistSaved(artistData.name);
      
      return {
        success: true,
        action: 'created',
        artist: artistData.name
      };
      
    } catch (error) {
      console.error(`❌ Artist creation failed for ${artistData.name}:`, error);
      console.error(`❌ Error stack:`, error.stack);
      
      // Take a screenshot of the current state
      try {
        await this.page.screenshot({ path: `./test-results/debug-create-error-${Date.now()}.png`, fullPage: true });
        console.log(`📸 Error screenshot saved`);
      } catch (screenshotError) {
        console.warn(`Could not take error screenshot:`, screenshotError.message);
      }
      
      return {
        success: false,
        action: 'create_failed',
        artist: artistData.name,
        error: error.message
      };
    }
  }

  /**
   * Update an existing artist with changed fields only
   * @param {Object} artistSummary - Artist summary from search
   * @param {Object} testData - Test data to update to
   * @returns {Object} Update result
   */
  async updateArtist(artistSummary, testData) {
    try {
      console.log(`🔄 Updating artist: ${artistSummary.name}`);
      
      // Get current artist data
      const currentData = await this.getArtistData(artistSummary);
      if (!currentData) {
        throw new Error('Could not retrieve current artist data');
      }
      
      // Compare data
      const comparison = compareArtistData(testData, currentData);
      
      if (!comparison.hasChanges) {
        console.log(`✅ No changes needed for ${artistSummary.name}`);
        return {
          success: true,
          action: 'no_changes',
          artist: artistSummary.name
        };
      }
      
      console.log(generateChangeSummary(comparison, artistSummary.name));
      
      // Update only changed fields
      const updateData = {};
      for (const field of comparison.changedFields) {
        updateData[field] = testData[field];
      }
      
      // Fill form with updates
      await this.fillArtistForm(updateData, true); // partial update
      
      // Save
      await this.saveArtistForm();
      
      // Verify success
      await this.verifyArtistSaved(artistSummary.name);
      
      return {
        success: true,
        action: 'updated',
        artist: artistSummary.name,
        changedFields: comparison.changedFields
      };
      
    } catch (error) {
      return {
        success: false,
        action: 'update_failed',
        artist: artistSummary.name,
        error: error.message
      };
    }
  }

  /**
   * Process a single artist: search, create, or update as needed
   * @param {Object} testData - Artist data from test configuration
   * @returns {Object} Processing result
   */
  async processArtist(testData) {
    try {
      // Search for existing artist
      const searchResult = await this.searchArtist(testData.name);
      
      if (!searchResult.found) {
        // Create new artist
        return await this.createArtist(testData);
      } else {
        // Update existing artist
        return await this.updateArtist(searchResult.artist, testData);
      }
      
    } catch (error) {
      return {
        success: false,
        action: 'process_failed',
        artist: testData.name,
        error: error.message
      };
    }
  }

  /**
   * Fill artist form with data
   * @param {Object} artistData - Data to fill
   * @param {boolean} isPartialUpdate - Whether this is a partial update
   */
  async fillArtistForm(artistData, isPartialUpdate = false) {
    console.log(`📝 Starting to fill form with data:`, JSON.stringify(artistData, null, 2));
    
    // Fill name (required)
    if (artistData.name) {
      console.log(`📝 Filling name field: ${artistData.name}`);
      await this.fillField('name', artistData.name);
    }
    
    // Fill bio
    if (artistData.bio !== undefined) {
      console.log(`📝 Filling bio field: ${artistData.bio || '(empty)'}`);
      await this.fillField('bio', artistData.bio || '');
    }
    
    // Fill website
    if (artistData.website !== undefined) {
      console.log(`📝 Filling website field: ${artistData.website || '(empty)'}`);
      await this.fillField('website', artistData.website || '');
    }
    
    // Fill birth year
    if (artistData.birth_year !== undefined) {
      const birthYear = artistData.birth_year ? artistData.birth_year.toString() : '';
      console.log(`📝 Filling birth_year field: ${birthYear || '(empty)'}`);
      await this.fillField('birth_year', birthYear);
    }
    
    console.log(`✅ Completed filling all form fields`);
  }

  /**
   * Fill a specific field with retry logic
   * @param {string} fieldName - Name of the field
   * @param {string} value - Value to fill
   */
  async fillField(fieldName, value) {
    try {
      let field = null;
      
      // Use getByRole approach which is more reliable for Wagtail forms
      switch (fieldName) {
        case 'name':
          field = this.page.getByRole('textbox', { name: 'Name*' });
          break;
        case 'bio':
          field = this.page.getByRole('textbox', { name: 'Bio' });
          break;
        case 'website':
          field = this.page.getByRole('textbox', { name: 'Website' });
          break;
        case 'birth_year':
          field = this.page.getByRole('spinbutton', { name: 'Birth year' });
          break;
        default:
          throw new Error(`Unknown field: ${fieldName}`);
      }
      
      // Wait for the field to be available
      await field.waitFor({ timeout: 5000 });
      
      // Clear and fill the field
      await field.clear();
      if (value) {
        await field.fill(value);
      }
      
      console.log(`✅ Successfully filled ${fieldName} with: ${value}`);
      
    } catch (error) {
      console.warn(`❌ Could not find field: ${fieldName}. Error: ${error.message}`);
      throw error;
    }
  }

  /**
   * Save the artist form
   */
  async saveArtistForm() {
    try {
      // Use getByRole for more reliable button detection
      const saveButton = this.page.getByRole('button', { name: 'Save' });
      await saveButton.waitFor({ timeout: 5000 });
      
      console.log(`✅ Found save button`);
      await saveButton.click();
      await this.page.waitForLoadState('networkidle');
      
    } catch (error) {
      console.warn(`❌ Could not find save button. Error: ${error.message}`);
      throw new Error('Could not find save button');
    }
  }

  /**
   * Verify that an artist was saved successfully
   * @param {string} artistName - Name of the artist to verify
   */
  async verifyArtistSaved(artistName) {
    try {
      // Look for success message
      const successMessage = this.page.locator('.success, .messages .success, .message-success');
      if (await successMessage.count() > 0) {
        return;
      }
      
      // If no success message, check if we're redirected to listing
      await this.page.waitForTimeout(2000);
      const currentUrl = this.page.url();
      
      if (currentUrl.includes('/add/')) {
        throw new Error('Still on add page - save may have failed');
      }
      
      // Additional verification: search for the artist
      const searchResult = await this.searchArtist(artistName);
      if (!searchResult.found) {
        throw new Error('Artist not found after save');
      }
      
    } catch (error) {
      throw new Error(`Save verification failed: ${error.message}`);
    }
  }

  /**
   * Extract artist ID from edit URL
   * @param {string} url - Edit URL
   * @returns {string|null} Artist ID
   */
  extractArtistIdFromUrl(url) {
    const match = url.match(/\/edit\/(\d+)\//);
    return match ? match[1] : null;
  }

  /**
   * Calculate similarity between two strings
   * @param {string} str1 - First string
   * @param {string} str2 - Second string
   * @returns {number} Similarity score between 0 and 1
   */
  calculateSimilarity(str1, str2) {
    if (str1 === str2) return 1;
    
    const maxLength = Math.max(str1.length, str2.length);
    if (maxLength === 0) return 1;
    
    const editDistance = this.levenshteinDistance(str1, str2);
    return (maxLength - editDistance) / maxLength;
  }

  /**
   * Calculate Levenshtein distance
   * @param {string} str1 - First string
   * @param {string} str2 - Second string
   * @returns {number} Edit distance
   */
  levenshteinDistance(str1, str2) {
    const matrix = [];
    
    for (let i = 0; i <= str2.length; i++) {
      matrix[i] = [i];
    }
    
    for (let j = 0; j <= str1.length; j++) {
      matrix[0][j] = j;
    }
    
    for (let i = 1; i <= str2.length; i++) {
      for (let j = 1; j <= str1.length; j++) {
        if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j] + 1
          );
        }
      }
    }
    
    return matrix[str2.length][str1.length];
  }
}