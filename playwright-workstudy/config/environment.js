import dotenv from 'dotenv';
import path from 'path';

// Load environment variables
dotenv.config();

/**
 * Environment configuration management
 */
export class Environment {
  static get wagtail() {
    return {
      baseUrl: process.env.WAGTAIL_BASE_URL || 'http://localhost:8000',
      adminUrl: process.env.WAGTAIL_ADMIN_URL || '/admin/',
      user: process.env.WAGTAIL_USER || 'admin',
      password: process.env.WAGTAIL_PASS || 'password',
    };
  }

  static get development() {
    return {
      mode: process.env.DEV_MODE || 'local-offline',
      nodeEnv: process.env.NODE_ENV || 'development',
      composeFileOffline: process.env.COMPOSE_FILE_OFFLINE || '../compose/compose.local-offline.yml',
      composeFileCloud: process.env.COMPOSE_FILE_CLOUD || '../compose/compose.local-cloud.yml',
    };
  }

  static get batch() {
    return {
      defaultSize: parseInt(process.env.DEFAULT_BATCH_SIZE) || 20,
      maxRetries: parseInt(process.env.MAX_RETRIES) || 3,
      retryDelay: parseInt(process.env.RETRY_DELAY) || 2000,
    };
  }

  static get logging() {
    return {
      level: process.env.LOG_LEVEL || 'info',
      enableProgressTracking: process.env.ENABLE_PROGRESS_TRACKING === 'true',
    };
  }

  static get browser() {
    return {
      headless: process.env.HEADLESS !== 'false',
      slowMo: parseInt(process.env.SLOW_MO) || 0,
      timeout: parseInt(process.env.BROWSER_TIMEOUT) || 30000,
    };
  }

  static get paths() {
    return {
      auth: './auth/auth.json',
      data: './data',
      reports: './reports',
      progress: './reports/progress',
    };
  }

  /**
   * Get full admin URL
   */
  static getAdminUrl(path = '') {
    const baseUrl = this.wagtail.baseUrl.replace(/\/$/, '');
    const adminUrl = this.wagtail.adminUrl.replace(/^\/|\/$/g, '');
    const cleanPath = path.replace(/^\//, '');
    
    return `${baseUrl}/${adminUrl}${cleanPath ? '/' + cleanPath : ''}`;
  }

  /**
   * Validate required environment variables
   */
  static validate() {
    const required = [
      'WAGTAIL_BASE_URL',
      'WAGTAIL_USER',
      'WAGTAIL_PASS'
    ];

    const missing = required.filter(key => !process.env[key]);
    
    if (missing.length > 0) {
      throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
    }

    return true;
  }

  /**
   * Get environment info for logging
   */
  static getInfo() {
    return {
      baseUrl: this.wagtail.baseUrl,
      devMode: this.development.mode,
      nodeEnv: this.development.nodeEnv,
      batchSize: this.batch.defaultSize,
      headless: this.browser.headless,
    };
  }
}