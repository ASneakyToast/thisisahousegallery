import fs from 'fs-extra';
import path from 'path';
import { Environment } from '../config/environment.js';

/**
 * Data loader utility for managing artist and artwork data
 */
export class DataLoader {
  static dataPath = path.resolve(Environment.paths.data);

  /**
   * Load artists data with optional slicing
   * @param {number} startIndex - Starting index (default: 0)
   * @param {number} endIndex - Ending index (default: load all)
   * @returns {Array} Array of artist objects
   */
  static async loadArtists(startIndex = 0, endIndex = null) {
    try {
      const filePath = path.join(this.dataPath, 'artists.json');
      const data = await fs.readJson(filePath);
      
      if (endIndex !== null) {
        return data.slice(startIndex, endIndex);
      }
      
      return data.slice(startIndex);
    } catch (error) {
      throw new Error(`Failed to load artists data: ${error.message}`);
    }
  }

  /**
   * Load artworks data with optional slicing
   * @param {number} startIndex - Starting index (default: 0)
   * @param {number} endIndex - Ending index (default: load all)
   * @returns {Array} Array of artwork objects
   */
  static async loadArtworks(startIndex = 0, endIndex = null) {
    try {
      const filePath = path.join(this.dataPath, 'artworks.json');
      const data = await fs.readJson(filePath);
      
      if (endIndex !== null) {
        return data.slice(startIndex, endIndex);
      }
      
      return data.slice(startIndex);
    } catch (error) {
      throw new Error(`Failed to load artworks data: ${error.message}`);
    }
  }

  /**
   * Get a specific artist by ID
   * @param {string} artistId - The artist ID to find
   * @returns {Object|null} Artist object or null if not found
   */
  static async getArtistById(artistId) {
    try {
      const artists = await this.loadArtists();
      return artists.find(artist => artist.id === artistId) || null;
    } catch (error) {
      throw new Error(`Failed to get artist by ID: ${error.message}`);
    }
  }

  /**
   * Get a specific artwork by ID
   * @param {string} artworkId - The artwork ID to find
   * @returns {Object|null} Artwork object or null if not found
   */
  static async getArtworkById(artworkId) {
    try {
      const artworks = await this.loadArtworks();
      return artworks.find(artwork => artwork.id === artworkId) || null;
    } catch (error) {
      throw new Error(`Failed to get artwork by ID: ${error.message}`);
    }
  }

  /**
   * Get all artworks by a specific artist
   * @param {string} artistId - The artist ID
   * @returns {Array} Array of artwork objects
   */
  static async getArtworksByArtist(artistId) {
    try {
      const artworks = await this.loadArtworks();
      return artworks.filter(artwork => artwork.artist_id === artistId);
    } catch (error) {
      throw new Error(`Failed to get artworks by artist: ${error.message}`);
    }
  }

  /**
   * Get batch of artists for processing
   * @param {number} batchNumber - Batch number (1-based)
   * @param {number} batchSize - Size of each batch (default from environment)
   * @returns {Array} Array of artist objects
   */
  static async getArtistBatch(batchNumber, batchSize = Environment.batch.defaultSize) {
    const startIndex = (batchNumber - 1) * batchSize;
    const endIndex = startIndex + batchSize;
    
    return await this.loadArtists(startIndex, endIndex);
  }

  /**
   * Get batch of artworks for processing
   * @param {number} batchNumber - Batch number (1-based)
   * @param {number} batchSize - Size of each batch (default from environment)
   * @returns {Array} Array of artwork objects
   */
  static async getArtworkBatch(batchNumber, batchSize = Environment.batch.defaultSize) {
    const startIndex = (batchNumber - 1) * batchSize;
    const endIndex = startIndex + batchSize;
    
    return await this.loadArtworks(startIndex, endIndex);
  }

  /**
   * Get total count of artists
   * @returns {number} Total number of artists
   */
  static async getArtistCount() {
    try {
      const artists = await this.loadArtists();
      return artists.length;
    } catch (error) {
      throw new Error(`Failed to get artist count: ${error.message}`);
    }
  }

  /**
   * Get total count of artworks
   * @returns {number} Total number of artworks
   */
  static async getArtworkCount() {
    try {
      const artworks = await this.loadArtworks();
      return artworks.length;
    } catch (error) {
      throw new Error(`Failed to get artwork count: ${error.message}`);
    }
  }

  /**
   * Calculate total number of batches needed
   * @param {string} type - 'artists' or 'artworks'
   * @param {number} batchSize - Size of each batch
   * @returns {number} Total number of batches
   */
  static async calculateBatchCount(type, batchSize = Environment.batch.defaultSize) {
    try {
      const count = type === 'artists' ? await this.getArtistCount() : await this.getArtworkCount();
      return Math.ceil(count / batchSize);
    } catch (error) {
      throw new Error(`Failed to calculate batch count: ${error.message}`);
    }
  }

  /**
   * Validate data integrity
   * @returns {Object} Validation results
   */
  static async validateData() {
    try {
      const artists = await this.loadArtists();
      const artworks = await this.loadArtworks();
      
      const results = {
        valid: true,
        errors: [],
        warnings: [],
        stats: {
          artistCount: artists.length,
          artworkCount: artworks.length
        }
      };

      // Check for duplicate artist IDs
      const artistIds = artists.map(a => a.id);
      const duplicateArtistIds = artistIds.filter((id, index) => artistIds.indexOf(id) !== index);
      if (duplicateArtistIds.length > 0) {
        results.valid = false;
        results.errors.push(`Duplicate artist IDs: ${duplicateArtistIds.join(', ')}`);
      }

      // Check for duplicate artwork IDs
      const artworkIds = artworks.map(a => a.id);
      const duplicateArtworkIds = artworkIds.filter((id, index) => artworkIds.indexOf(id) !== index);
      if (duplicateArtworkIds.length > 0) {
        results.valid = false;
        results.errors.push(`Duplicate artwork IDs: ${duplicateArtworkIds.join(', ')}`);
      }

      // Check for missing artist references
      const orphanedArtworks = artworks.filter(artwork => {
        return artwork.artist_id && !artistIds.includes(artwork.artist_id);
      });
      if (orphanedArtworks.length > 0) {
        results.warnings.push(`${orphanedArtworks.length} artworks reference non-existent artists`);
      }

      // Check for required fields
      const artistsWithoutNames = artists.filter(a => !a.name);
      if (artistsWithoutNames.length > 0) {
        results.valid = false;
        results.errors.push(`${artistsWithoutNames.length} artists missing required name field`);
      }

      const artworksWithoutTitles = artworks.filter(a => !a.title);
      if (artworksWithoutTitles.length > 0) {
        results.valid = false;
        results.errors.push(`${artworksWithoutTitles.length} artworks missing required title field`);
      }

      return results;
    } catch (error) {
      return {
        valid: false,
        errors: [`Data validation failed: ${error.message}`],
        warnings: [],
        stats: {}
      };
    }
  }

  /**
   * Get data summary for reporting
   * @returns {Object} Data summary
   */
  static async getDataSummary() {
    try {
      const validation = await this.validateData();
      const batchSize = Environment.batch.defaultSize;
      
      return {
        artists: {
          total: validation.stats.artistCount,
          batches: await this.calculateBatchCount('artists', batchSize),
          batchSize: batchSize
        },
        artworks: {
          total: validation.stats.artworkCount,
          batches: await this.calculateBatchCount('artworks', batchSize),
          batchSize: batchSize
        },
        validation: {
          valid: validation.valid,
          errorCount: validation.errors.length,
          warningCount: validation.warnings.length
        }
      };
    } catch (error) {
      throw new Error(`Failed to get data summary: ${error.message}`);
    }
  }
}