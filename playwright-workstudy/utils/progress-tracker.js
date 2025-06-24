import fs from 'fs-extra';
import path from 'path';
import { Environment } from '../config/environment.js';
import { Logger } from './logger.js';

/**
 * Progress tracking utility for batch operations
 */
export class ProgressTracker {
  static progressDir = path.resolve(Environment.paths.progress);

  /**
   * Initialize progress tracking
   */
  static async initialize() {
    try {
      await fs.ensureDir(this.progressDir);
      Logger.debug('Progress tracking initialized');
    } catch (error) {
      Logger.error('Failed to initialize progress tracking', error);
      throw error;
    }
  }

  /**
   * Get progress file path for a specific type and batch
   * @param {string} type - Type of operation (artists, artworks)
   * @param {number} batchNumber - Batch number
   * @returns {string} Progress file path
   */
  static getProgressFile(type, batchNumber) {
    return path.join(this.progressDir, `${type}-batch-${batchNumber}.json`);
  }

  /**
   * Save progress for a batch
   * @param {string} type - Type of operation (artists, artworks)
   * @param {number} batchNumber - Batch number
   * @param {Object} progress - Progress data
   */
  static async saveProgress(type, batchNumber, progress) {
    if (!Environment.logging.enableProgressTracking) return;

    try {
      await this.initialize();
      
      const progressFile = this.getProgressFile(type, batchNumber);
      const progressData = {
        type,
        batchNumber,
        timestamp: new Date().toISOString(),
        ...progress
      };
      
      await fs.writeJson(progressFile, progressData, { spaces: 2 });
      Logger.debug(`Progress saved for ${type} batch ${batchNumber}`);
    } catch (error) {
      Logger.error('Failed to save progress', error);
    }
  }

  /**
   * Load progress for a batch
   * @param {string} type - Type of operation (artists, artworks)
   * @param {number} batchNumber - Batch number
   * @returns {Object|null} Progress data or null if not found
   */
  static async loadProgress(type, batchNumber) {
    if (!Environment.logging.enableProgressTracking) return null;

    try {
      const progressFile = this.getProgressFile(type, batchNumber);
      
      if (await fs.pathExists(progressFile)) {
        const progress = await fs.readJson(progressFile);
        Logger.debug(`Progress loaded for ${type} batch ${batchNumber}`);
        return progress;
      }
      
      return null;
    } catch (error) {
      Logger.error('Failed to load progress', error);
      return null;
    }
  }

  /**
   * Clear progress for a batch
   * @param {string} type - Type of operation (artists, artworks)
   * @param {number} batchNumber - Batch number
   */
  static async clearProgress(type, batchNumber) {
    if (!Environment.logging.enableProgressTracking) return;

    try {
      const progressFile = this.getProgressFile(type, batchNumber);
      
      if (await fs.pathExists(progressFile)) {
        await fs.remove(progressFile);
        Logger.debug(`Progress cleared for ${type} batch ${batchNumber}`);
      }
    } catch (error) {
      Logger.error('Failed to clear progress', error);
    }
  }

  /**
   * Get all progress files
   * @returns {Array} Array of progress file information
   */
  static async getAllProgress() {
    if (!Environment.logging.enableProgressTracking) return [];

    try {
      await this.initialize();
      
      const files = await fs.readdir(this.progressDir);
      const progressFiles = [];
      
      for (const file of files) {
        if (file.endsWith('.json')) {
          const filePath = path.join(this.progressDir, file);
          try {
            const progress = await fs.readJson(filePath);
            progressFiles.push({
              file,
              path: filePath,
              ...progress
            });
          } catch (error) {
            Logger.warn(`Failed to read progress file: ${file}`, error);
          }
        }
      }
      
      return progressFiles.sort((a, b) => {
        if (a.type !== b.type) {
          return a.type.localeCompare(b.type);
        }
        return a.batchNumber - b.batchNumber;
      });
    } catch (error) {
      Logger.error('Failed to get all progress', error);
      return [];
    }
  }

  /**
   * Generate progress summary
   * @returns {Object} Progress summary
   */
  static async getProgressSummary() {
    try {
      const allProgress = await this.getAllProgress();
      
      const summary = {
        totalBatches: allProgress.length,
        artists: {
          batches: allProgress.filter(p => p.type === 'artists').length,
          completed: allProgress.filter(p => p.type === 'artists' && p.status === 'completed').length,
          inProgress: allProgress.filter(p => p.type === 'artists' && p.status === 'in_progress').length,
          failed: allProgress.filter(p => p.type === 'artists' && p.status === 'failed').length
        },
        artworks: {
          batches: allProgress.filter(p => p.type === 'artworks').length,
          completed: allProgress.filter(p => p.type === 'artworks' && p.status === 'completed').length,
          inProgress: allProgress.filter(p => p.type === 'artworks' && p.status === 'in_progress').length,
          failed: allProgress.filter(p => p.type === 'artworks' && p.status === 'failed').length
        },
        lastUpdated: allProgress.length > 0 ? 
          allProgress.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))[0].timestamp : null
      };
      
      return summary;
    } catch (error) {
      Logger.error('Failed to get progress summary', error);
      return {
        totalBatches: 0,
        artists: { batches: 0, completed: 0, inProgress: 0, failed: 0 },
        artworks: { batches: 0, completed: 0, inProgress: 0, failed: 0 },
        lastUpdated: null
      };
    }
  }

  /**
   * Create a batch tracker for monitoring individual batch progress
   * @param {string} type - Type of operation (artists, artworks)
   * @param {number} batchNumber - Batch number
   * @param {number} totalItems - Total items in batch
   * @returns {BatchTracker} Batch tracker instance
   */
  static createBatchTracker(type, batchNumber, totalItems) {
    return new BatchTracker(type, batchNumber, totalItems);
  }

  /**
   * Clean up old progress files
   * @param {number} maxAge - Maximum age in days (default: 7)
   */
  static async cleanup(maxAge = 7) {
    if (!Environment.logging.enableProgressTracking) return;

    try {
      const allProgress = await this.getAllProgress();
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - maxAge);
      
      let cleaned = 0;
      
      for (const progress of allProgress) {
        const progressDate = new Date(progress.timestamp);
        
        if (progressDate < cutoffDate) {
          await fs.remove(progress.path);
          cleaned++;
        }
      }
      
      if (cleaned > 0) {
        Logger.info(`Cleaned up ${cleaned} old progress files`);
      }
    } catch (error) {
      Logger.error('Failed to cleanup progress files', error);
    }
  }
}

/**
 * Individual batch tracker for real-time progress monitoring
 */
export class BatchTracker {
  constructor(type, batchNumber, totalItems) {
    this.type = type;
    this.batchNumber = batchNumber;
    this.totalItems = totalItems;
    this.completed = [];
    this.failed = [];
    this.skipped = [];
    this.startTime = new Date();
    this.status = 'in_progress';
  }

  /**
   * Mark an item as completed
   * @param {string} itemId - Item identifier
   * @param {Object} details - Additional details
   */
  async markCompleted(itemId, details = {}) {
    this.completed.push({
      id: itemId,
      timestamp: new Date().toISOString(),
      ...details
    });
    
    await this.saveProgress();
    Logger.progress(
      `Completed ${this.type.slice(0, -1)}: ${itemId}`,
      this.completed.length + this.failed.length + this.skipped.length,
      this.totalItems
    );
  }

  /**
   * Mark an item as failed
   * @param {string} itemId - Item identifier
   * @param {string} error - Error message
   * @param {Object} details - Additional details
   */
  async markFailed(itemId, error, details = {}) {
    this.failed.push({
      id: itemId,
      error,
      timestamp: new Date().toISOString(),
      ...details
    });
    
    await this.saveProgress();
    Logger.error(`Failed ${this.type.slice(0, -1)}: ${itemId} - ${error}`);
  }

  /**
   * Mark an item as skipped
   * @param {string} itemId - Item identifier
   * @param {string} reason - Skip reason
   * @param {Object} details - Additional details
   */
  async markSkipped(itemId, reason, details = {}) {
    this.skipped.push({
      id: itemId,
      reason,
      timestamp: new Date().toISOString(),
      ...details
    });
    
    await this.saveProgress();
    Logger.skip(`Skipped ${this.type.slice(0, -1)}: ${itemId} - ${reason}`);
  }

  /**
   * Complete the batch
   */
  async complete() {
    this.status = 'completed';
    this.endTime = new Date();
    this.duration = this.endTime - this.startTime;
    
    await this.saveProgress();
    Logger.completeBatch(
      this.type,
      this.batchNumber,
      this.completed.length,
      this.failed.length,
      this.skipped.length
    );
  }

  /**
   * Mark batch as failed
   * @param {string} error - Error message
   */
  async fail(error) {
    this.status = 'failed';
    this.endTime = new Date();
    this.duration = this.endTime - this.startTime;
    this.batchError = error;
    
    await this.saveProgress();
    Logger.error(`Batch ${this.batchNumber} failed: ${error}`);
  }

  /**
   * Save current progress
   */
  async saveProgress() {
    const progressData = {
      status: this.status,
      totalItems: this.totalItems,
      completed: this.completed,
      failed: this.failed,
      skipped: this.skipped,
      startTime: this.startTime.toISOString(),
      endTime: this.endTime ? this.endTime.toISOString() : null,
      duration: this.duration,
      batchError: this.batchError
    };
    
    await ProgressTracker.saveProgress(this.type, this.batchNumber, progressData);
  }

  /**
   * Get current progress statistics
   * @returns {Object} Progress statistics
   */
  getStats() {
    const processed = this.completed.length + this.failed.length + this.skipped.length;
    const remaining = this.totalItems - processed;
    const percentage = this.totalItems > 0 ? Math.round((processed / this.totalItems) * 100) : 0;
    
    return {
      processed,
      remaining,
      percentage,
      completed: this.completed.length,
      failed: this.failed.length,
      skipped: this.skipped.length,
      total: this.totalItems,
      status: this.status
    };
  }
}