import { test as setup, expect } from '@playwright/test';
import { Environment } from '../config/environment.js';

const authFile = Environment.paths.auth;

setup('authenticate', async ({ page }) => {
  // Navigate to login page
  const loginUrl = Environment.getAdminUrl('login/');
  await page.goto(loginUrl);

  // Check if already logged in
  if (page.url().includes('/admin/') && !page.url().includes('/login/')) {
    console.log('Already authenticated');
    return;
  }

  // Fill login form
  await page.waitForSelector('input[name="username"], input[name="login"]');
  
  const usernameField = page.locator('input[name="username"], input[name="login"]').first();
  await usernameField.fill(Environment.wagtail.user);
  
  await page.locator('input[name="password"]').fill(Environment.wagtail.password);
  
  // Submit form
  await page.locator('button[type="submit"], input[type="submit"]').click();
  
  // Wait for successful login
  await page.waitForURL('**/admin/**');
  
  // Verify we're logged in by checking for admin elements
  await expect(page.locator('.wagtail-logo, .header-logo, h1')).toBeVisible();

  // Save signed-in state
  await page.context().storageState({ path: authFile });
});