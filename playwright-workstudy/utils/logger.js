import fs from 'fs-extra';
import path from 'path';
import { Environment } from '../config/environment.js';

/**
 * Logger utility for Playwright CMS automation
 */
export class Logger {
  static logLevel = Environment.logging.level;
  static enableProgressTracking = Environment.logging.enableProgressTracking;
  
  static levels = {
    error: 0,
    warn: 1,
    info: 2,
    debug: 3
  };

  static colors = {
    error: '\x1b[31m', // Red
    warn: '\x1b[33m',  // Yellow
    info: '\x1b[36m',  // Cyan
    debug: '\x1b[37m', // White
    success: '\x1b[32m', // Green
    reset: '\x1b[0m'
  };

  static icons = {
    error: '❌',
    warn: '⚠️',
    info: 'ℹ️',
    debug: '🔍',
    success: '✅',
    progress: '⏳',
    skip: '⏭️',
    create: '🆕',
    update: '📝',
    delete: '🗑️'
  };

  /**
   * Log a message with level checking
   * @param {string} level - Log level
   * @param {string} message - Message to log
   * @param {Object} data - Additional data to log
   */
  static log(level, message, data = null) {
    if (this.levels[level] <= this.levels[this.logLevel]) {
      const timestamp = new Date().toISOString();
      const icon = this.icons[level] || '';
      const color = this.colors[level] || '';
      const reset = this.colors.reset;
      
      let logMessage = `${color}${icon} [${timestamp}] ${level.toUpperCase()}: ${message}${reset}`;
      
      if (data) {
        logMessage += `\n${JSON.stringify(data, null, 2)}`;
      }
      
      console.log(logMessage);
    }
  }

  /**
   * Log error message
   * @param {string} message - Error message
   * @param {Error|Object} error - Error object or additional data
   */
  static error(message, error = null) {
    this.log('error', message, error);
  }

  /**
   * Log warning message
   * @param {string} message - Warning message
   * @param {Object} data - Additional data
   */
  static warn(message, data = null) {
    this.log('warn', message, data);
  }

  /**
   * Log info message
   * @param {string} message - Info message
   * @param {Object} data - Additional data
   */
  static info(message, data = null) {
    this.log('info', message, data);
  }

  /**
   * Log debug message
   * @param {string} message - Debug message
   * @param {Object} data - Additional data
   */
  static debug(message, data = null) {
    this.log('debug', message, data);
  }

  /**
   * Log success message
   * @param {string} message - Success message
   * @param {Object} data - Additional data
   */
  static success(message, data = null) {
    const timestamp = new Date().toISOString();
    const icon = this.icons.success;
    const color = this.colors.success;
    const reset = this.colors.reset;
    
    let logMessage = `${color}${icon} [${timestamp}] SUCCESS: ${message}${reset}`;
    
    if (data) {
      logMessage += `\n${JSON.stringify(data, null, 2)}`;
    }
    
    console.log(logMessage);
  }

  /**
   * Log progress update
   * @param {string} message - Progress message
   * @param {number} current - Current item number
   * @param {number} total - Total items
   * @param {Object} data - Additional data
   */
  static progress(message, current = null, total = null, data = null) {
    if (!this.enableProgressTracking) return;
    
    const timestamp = new Date().toISOString();
    const icon = this.icons.progress;
    const color = this.colors.info;
    const reset = this.colors.reset;
    
    let progressText = '';
    if (current !== null && total !== null) {
      const percentage = Math.round((current / total) * 100);
      progressText = ` [${current}/${total} - ${percentage}%]`;
    }
    
    let logMessage = `${color}${icon} [${timestamp}] PROGRESS${progressText}: ${message}${reset}`;
    
    if (data) {
      logMessage += `\n${JSON.stringify(data, null, 2)}`;
    }
    
    console.log(logMessage);
  }

  /**
   * Log skip message
   * @param {string} message - Skip message
   * @param {Object} data - Additional data
   */
  static skip(message, data = null) {
    const timestamp = new Date().toISOString();
    const icon = this.icons.skip;
    const color = this.colors.warn;
    const reset = this.colors.reset;
    
    let logMessage = `${color}${icon} [${timestamp}] SKIP: ${message}${reset}`;
    
    if (data) {
      logMessage += `\n${JSON.stringify(data, null, 2)}`;
    }
    
    console.log(logMessage);
  }

  /**
   * Log batch start
   * @param {string} type - Type of batch (artists, artworks)
   * @param {number} batchNumber - Batch number
   * @param {number} batchSize - Batch size
   */
  static startBatch(type, batchNumber, batchSize) {
    const startIndex = (batchNumber - 1) * batchSize + 1;
    const endIndex = batchNumber * batchSize;
    
    this.info(`Starting ${type} batch ${batchNumber} (items ${startIndex}-${endIndex})`);
  }

  /**
   * Log batch completion
   * @param {string} type - Type of batch (artists, artworks)
   * @param {number} batchNumber - Batch number
   * @param {number} successful - Number of successful operations
   * @param {number} failed - Number of failed operations
   * @param {number} skipped - Number of skipped operations
   */
  static completeBatch(type, batchNumber, successful, failed, skipped) {
    const total = successful + failed + skipped;
    this.success(`Completed ${type} batch ${batchNumber}: ${successful} created, ${skipped} skipped, ${failed} failed (${total} total)`);
  }
}