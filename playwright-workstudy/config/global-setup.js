import { chromium } from '@playwright/test';
import { Environment } from './environment.js';
import fs from 'fs-extra';
import path from 'path';

/**
 * Global setup function that runs before all tests
 * Handles authentication and initial setup
 */
async function globalSetup() {
  console.log('🚀 Starting global setup...');
  
  try {
    // Validate environment variables
    Environment.validate();
    
    // Log environment info
    const envInfo = Environment.getInfo();
    console.log('📊 Environment Info:', envInfo);
    
    // Ensure auth directory exists
    await fs.ensureDir(path.dirname(Environment.paths.auth));
    
    // Launch browser for authentication
    const browser = await chromium.launch({
      headless: Environment.browser.headless,
      slowMo: Environment.browser.slowMo,
    });
    
    const context = await browser.newContext({
      viewport: { width: 1280, height: 720 },
      ignoreHTTPSErrors: true,
    });
    
    const page = await context.newPage();
    
    // Navigate to Wagtail admin login
    const loginUrl = Environment.getAdminUrl('login/');
    console.log(`🔐 Navigating to login: ${loginUrl}`);
    
    await page.goto(loginUrl, { waitUntil: 'networkidle' });
    
    // Check if already logged in (redirect to admin dashboard)
    if (page.url().includes('/admin/') && !page.url().includes('/login/')) {
      console.log('✅ Already authenticated');
    } else {
      // Fill login form
      console.log('📝 Filling login form...');
      
      // Wait for login form elements
      await page.waitForSelector('input[name="username"], input[name="login"]', { timeout: 10000 });
      
      // Try different possible username field names
      const usernameSelector = await page.locator('input[name="username"], input[name="login"]').first();
      await usernameSelector.fill(Environment.wagtail.user);
      
      // Fill password
      await page.locator('input[name="password"]').fill(Environment.wagtail.password);
      
      // Submit form
      await page.locator('button[type="submit"], input[type="submit"]').click();
      
      // Wait for navigation to admin dashboard
      await page.waitForURL('**/admin/**', { timeout: 15000 });
      console.log('✅ Successfully authenticated');
    }
    
    // Verify we're on the admin dashboard
    await page.waitForSelector('.wagtail-logo, .header-logo, h1', { timeout: 10000 });
    
    // Save authentication state
    await context.storageState({ path: Environment.paths.auth });
    console.log(`💾 Authentication state saved to: ${Environment.paths.auth}`);
    
    // Clean up
    await context.close();
    await browser.close();
    
    console.log('✅ Global setup completed successfully');
    
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  }
}

export default globalSetup;