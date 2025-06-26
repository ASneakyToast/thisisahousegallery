import { test, expect } from '@playwright/test';
import { Logger } from '../../utils/logger.js';
import { HomepageOperations } from './homepage-operations.js';
import fs from 'fs';
import path from 'path';

/**
 * Homepage Initialization Test Suite
 * 
 * Comprehensive test that initializes the homepage:
 * - Deletes default Wagtail welcome page
 * - Creates new HomePage with Hero section
 * - Adds intro text and call-to-action links
 * - Verifies homepage displays correctly
 */

test.describe('Homepage Initialization', () => {
  let homepageConfig;
  
  test.beforeAll(async () => {
    Logger.info('🏠 Starting Homepage Initialization Test Suite');
    
    // Load homepage configuration
    const configPath = path.join(process.cwd(), 'projects', 'homepage-initialization', 'test-data', 'homepage-content.json');
    const configData = fs.readFileSync(configPath, 'utf8');
    homepageConfig = JSON.parse(configData);
    
    Logger.info('📁 Loaded homepage configuration');
  });

  test.afterAll(async () => {
    Logger.info('✅ Homepage Initialization Test Suite completed');
  });

  test('Initialize homepage with complete workflow', async ({ page }) => {
    // Initialize operations
    const homepageOps = new HomepageOperations(page);
    
    const results = {
      deleted_pages: [],
      created_homepage: false,
      added_hero: false,
      verified: false,
      errors: []
    };
    
    try {
      Logger.info('🚀 Starting complete homepage initialization workflow');
      
      // Execute the complete workflow
      const workflowResult = await homepageOps.initializeHomepage(homepageConfig);
      
      // Update results from workflow
      if (workflowResult.success) {
        results.deleted_pages = workflowResult.results.deleted_pages;
        results.created_homepage = workflowResult.results.created_homepage;
        results.added_hero = workflowResult.results.added_hero;
        results.verified = workflowResult.results.verified;
      }
      
      // Generate comprehensive report
      await generateTestReport(results);
      
      // Assert that the workflow completed successfully
      expect(workflowResult.success).toBeTruthy();
      expect(results.created_homepage).toBeTruthy();
      
    } catch (error) {
      results.errors.push(error.message);
      Logger.error(`❌ Workflow failed: ${error.message}`);
      
      // Generate error report
      await generateTestReport(results);
      
      throw error;
    }
  });

  test('Verify homepage content and structure', async ({ page }) => {
    Logger.info('🔍 Verifying homepage content and structure');
    
    const homepageOps = new HomepageOperations(page);
    
    try {
      // Perform detailed verification
      const verification = await homepageOps.verifyHomePage(homepageConfig.homepage);
      
      // Additional content checks
      const contentChecks = await performContentValidation(page, homepageConfig.homepage);
      
      Logger.info(`📊 Verification Results:`);
      Logger.info(`   ✅ Basic verification: ${verification.success ? 'PASSED' : 'FAILED'}`);
      Logger.info(`   ✅ Content validation: ${contentChecks.passed}/${contentChecks.total} checks passed`);
      
      // Assert verification results
      expect(verification.success).toBeTruthy();
      expect(contentChecks.passed / contentChecks.total).toBeGreaterThanOrEqual(0.5); // At least 50% of checks should pass
      
    } catch (error) {
      Logger.error(`❌ Verification failed: ${error.message}`);
      throw error;
    }
  });

  test('Test individual homepage operations', async ({ page }) => {
    Logger.info('🧪 Testing individual homepage operations');
    
    const homepageOps = new HomepageOperations(page);
    
    try {
      // Test 1: Search for default pages
      Logger.info('🔍 Testing default page detection');
      const defaultPages = await homepageOps.findDefaultPages();
      Logger.info(`Found ${defaultPages.length} default pages`);
      
      // Test 2: Verify navigation to admin works
      Logger.info('🌐 Testing admin navigation');
      await page.goto(process.env.WAGTAIL_BASE_URL + '/admin/pages/');
      await page.waitForLoadState('networkidle');
      
      const pageTitle = await page.title();
      expect(pageTitle).toContain('Wagtail'); // Should be on Wagtail admin (Pages section)
      
      // Test 3: Verify we can access the homepage
      Logger.info('🏠 Testing homepage access');
      await page.goto(process.env.WAGTAIL_BASE_URL + '/');
      await page.waitForLoadState('networkidle');
      
      // Check that we get a valid response (not 404 or 500)
      const response = await page.goto(process.env.WAGTAIL_BASE_URL + '/');
      expect(response.status()).toBeLessThan(400);
      
      Logger.success('✅ All individual operations passed');
      
    } catch (error) {
      Logger.error(`❌ Individual operations test failed: ${error.message}`);
      throw error;
    }
  });
});

/**
 * Perform detailed content validation on the homepage
 * @param {Page} page - Playwright page object
 * @param {Object} homepageData - Expected homepage data
 * @returns {Object} Validation results
 */
async function performContentValidation(page, homepageData) {
  const checks = {
    total: 0,
    passed: 0,
    details: []
  };
  
  try {
    // Navigate to homepage
    await page.goto(process.env.WAGTAIL_BASE_URL + '/');
    await page.waitForLoadState('networkidle');
    
    // Check 1: Page title
    checks.total++;
    const pageTitle = await page.title();
    if (pageTitle.includes(homepageData.title) || pageTitle.includes('House Gallery')) {
      checks.passed++;
      checks.details.push({ check: 'Page title', status: 'PASSED', value: pageTitle });
      Logger.success('✅ Page title check passed');
    } else {
      checks.details.push({ check: 'Page title', status: 'FAILED', value: pageTitle });
      Logger.warn(`⚠️  Page title check failed: ${pageTitle}`);
    }
    
    // Check 2: Hero intro text (if configured)
    if (homepageData.hero && homepageData.hero.intro) {
      checks.total++;
      const introTextPart = homepageData.hero.intro.substring(0, 20);
      const introElement = page.locator(`text="${introTextPart}"`);
      
      if (await introElement.count() > 0) {
        checks.passed++;
        checks.details.push({ check: 'Hero intro text', status: 'PASSED' });
        Logger.success('✅ Hero intro text check passed');
      } else {
        checks.details.push({ check: 'Hero intro text', status: 'FAILED' });
        Logger.warn('⚠️  Hero intro text not found');
      }
    }
    
    // Check 3: CTA links (if configured)
    if (homepageData.hero && homepageData.hero.cta_links) {
      for (const ctaLink of homepageData.hero.cta_links) {
        checks.total++;
        const linkElement = page.locator(`text="${ctaLink.text}"`);
        
        if (await linkElement.count() > 0) {
          checks.passed++;
          checks.details.push({ check: `CTA link: ${ctaLink.text}`, status: 'PASSED' });
          Logger.success(`✅ CTA link check passed: ${ctaLink.text}`);
        } else {
          checks.details.push({ check: `CTA link: ${ctaLink.text}`, status: 'FAILED' });
          Logger.warn(`⚠️  CTA link not found: ${ctaLink.text}`);
        }
      }
    }
    
    // Check 4: Basic HTML structure
    checks.total++;
    const hasMainContent = await page.locator('main, [role="main"], .main-content').count() > 0;
    if (hasMainContent) {
      checks.passed++;
      checks.details.push({ check: 'Main content structure', status: 'PASSED' });
      Logger.success('✅ Main content structure check passed');
    } else {
      checks.details.push({ check: 'Main content structure', status: 'FAILED' });
      Logger.warn('⚠️  Main content structure not found');
    }
    
  } catch (error) {
    Logger.error(`❌ Content validation error: ${error.message}`);
    checks.details.push({ check: 'Content validation', status: 'ERROR', error: error.message });
  }
  
  return checks;
}

/**
 * Generate comprehensive test report
 * @param {Object} results - Test results
 */
async function generateTestReport(results) {
  Logger.info('\n' + '='.repeat(60));
  Logger.info('📊 HOMEPAGE INITIALIZATION TEST REPORT');
  Logger.info('='.repeat(60));
  
  // Summary statistics
  Logger.info(`📈 Summary Statistics:`);
  Logger.info(`   🗑️  Pages Deleted: ${results.deleted_pages.length}`);
  Logger.info(`   🏠 Homepage Created: ${results.created_homepage ? 'YES' : 'NO'}`);
  Logger.info(`   🎯 Hero Section Added: ${results.added_hero ? 'YES' : 'NO'}`);
  Logger.info(`   ✅ Verification Passed: ${results.verified ? 'YES' : 'NO'}`);
  Logger.info(`   ❌ Errors: ${results.errors.length}`);
  
  // Detailed breakdowns
  if (results.deleted_pages.length > 0) {
    Logger.info(`\n🗑️  Deleted Pages (${results.deleted_pages.length}):`);
    results.deleted_pages.forEach(page => {
      Logger.info(`   • ${page}`);
    });
  }
  
  if (results.errors.length > 0) {
    Logger.warn(`\n❌ Errors Encountered (${results.errors.length}):`);
    results.errors.forEach(error => {
      Logger.warn(`   • ${error}`);
    });
  }
  
  // Success assessment
  const overallSuccess = results.created_homepage && results.errors.length === 0;
  const successMessage = overallSuccess ? 
    '🎉 HOMEPAGE INITIALIZATION SUCCESSFUL' : 
    '⚠️  HOMEPAGE INITIALIZATION COMPLETED WITH ISSUES';
  
  Logger.info(`\n${overallSuccess ? '✅' : '⚠️ '} ${successMessage}`);
  
  Logger.info('\n' + '='.repeat(60));
  Logger.info('📁 Full report generated');
  Logger.info('='.repeat(60));
}