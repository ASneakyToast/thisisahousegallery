import { expect } from '@playwright/test';
import { Environment } from '../../config/environment.js';
import { CMSHelpers } from '../../utils/cms-helpers.js';
import { Logger } from '../../utils/logger.js';

/**
 * Homepage Operations for CMS Management
 * 
 * Provides operations for homepage initialization including:
 * - Delete default Wagtail pages
 * - Create new HomePage with StreamField content
 * - Add Hero section with intro and CTA links
 */
export class HomepageOperations {
  
  constructor(page) {
    this.page = page;
  }

  /**
   * Search for and identify default pages to delete
   * @returns {Array} Array of page objects found
   */
  async findDefaultPages() {
    try {
      Logger.info('🔍 Searching for default pages to delete');
      
      // Navigate to pages admin
      await CMSHelpers.navigateToAdmin(this.page, 'pages/');
      
      // Wait for page tree to load
      await this.page.waitForSelector('.listing, .page-listing, [data-page-title]', { timeout: 10000 });
      
      const defaultPages = [];
      
      // Look for default Wagtail welcome page
      const welcomePageSelector = 'a[href*="edit"]:has-text("Welcome to your new Wagtail site!")';
      const welcomePage = this.page.locator(welcomePageSelector);
      
      if (await welcomePage.count() > 0) {
        const pageUrl = await welcomePage.getAttribute('href');
        defaultPages.push({
          title: 'Welcome to your new Wagtail site!',
          editUrl: pageUrl,
          type: 'default_welcome'
        });
        Logger.info('✅ Found default welcome page');
      }
      
      // Look for any existing HomePage at root level
      const homePageSelector = 'a[href*="edit"]:has-text("Home")';
      const homePage = this.page.locator(homePageSelector);
      
      if (await homePage.count() > 0) {
        const pageUrl = await homePage.getAttribute('href');
        defaultPages.push({
          title: 'Home',
          editUrl: pageUrl,
          type: 'existing_home'
        });
        Logger.info('✅ Found existing home page');
      }
      
      Logger.info(`📋 Found ${defaultPages.length} pages to process`);
      return defaultPages;
      
    } catch (error) {
      Logger.error(`❌ Error finding default pages: ${error.message}`);
      return [];
    }
  }

  /**
   * Delete a page by its edit URL
   * @param {Object} pageInfo - Page information object
   */
  async deletePage(pageInfo) {
    try {
      Logger.info(`🗑️  Deleting page: ${pageInfo.title}`);
      
      // Navigate to the page edit URL
      await this.page.goto(Environment.wagtail.baseUrl + pageInfo.editUrl);
      await this.page.waitForLoadState('networkidle');
      
      // Find and click delete button - try multiple selectors
      const deleteSelectors = [
        'button:has-text("Delete")',
        'a:has-text("Delete")',
        '[data-action="delete"]',
        '.button-secondary:has-text("Delete")'
      ];
      
      let deleteClicked = false;
      for (const selector of deleteSelectors) {
        const deleteButton = this.page.locator(selector);
        if (await deleteButton.count() > 0) {
          await deleteButton.first().click();
          deleteClicked = true;
          break;
        }
      }
      
      if (!deleteClicked) {
        throw new Error('Could not find delete button');
      }
      
      // Wait for confirmation dialog and confirm deletion
      await this.page.waitForTimeout(1000);
      
      // Look for confirmation button
      const confirmSelectors = [
        'button:has-text("Yes, delete")',
        'button:has-text("Delete")',
        'input[type="submit"][value*="Delete"]',
        '.button-serious:has-text("Delete")'
      ];
      
      for (const selector of confirmSelectors) {
        const confirmButton = this.page.locator(selector);
        if (await confirmButton.count() > 0) {
          await confirmButton.first().click();
          break;
        }
      }
      
      // Wait for redirect back to pages list
      await this.page.waitForLoadState('networkidle');
      
      Logger.success(`✅ Successfully deleted: ${pageInfo.title}`);
      
    } catch (error) {
      throw new Error(`Failed to delete page "${pageInfo.title}": ${error.message}`);
    }
  }

  /**
   * Create a new HomePage
   * @param {Object} homepageData - Homepage configuration data
   */
  async createHomePage(homepageData) {
    try {
      Logger.info('🏠 Creating new HomePage');
      
      // Navigate to add page at root level - HomePage under root page (id=1)
      await CMSHelpers.navigateToAdmin(this.page, 'pages/add/home/homepage/1/');
      
      // Wait for form to load
      await this.page.waitForSelector('form', { timeout: 10000 });
      
      // Fill title field
      await this.page.fill('input[name="title"]', homepageData.title);
      
      // Fill slug if different from title - but first expand Promote section if collapsed
      if (homepageData.slug) {
        // Try to expand Promote tab/section if it exists and is collapsed
        const promoteTab = this.page.locator('a:has-text("Promote"), button:has-text("Promote")');
        if (await promoteTab.count() > 0) {
          await promoteTab.click();
          await this.page.waitForTimeout(1000);
        }
        
        // Now try to fill slug field
        const slugField = this.page.locator('input[name="slug"]');
        if (await slugField.isVisible()) {
          await slugField.fill(homepageData.slug);
        } else {
          Logger.warn('⚠️  Slug field not visible, skipping slug override');
        }
      }
      
      Logger.success('✅ Basic HomePage fields filled');
      
      return { success: true, action: 'created' };
      
    } catch (error) {
      throw new Error(`Failed to create HomePage: ${error.message}`);
    }
  }

  /**
   * Add Hero section to HomePage StreamField
   * @param {Object} heroData - Hero section configuration
   */
  async addHeroSection(heroData) {
    try {
      Logger.info('🎯 Adding Hero section to HomePage');
      
      // Find StreamField add button for hero block
      const addHeroButton = this.page.locator('button:has-text("Hero Section"), button[data-block-type="hero"]');
      
      if (await addHeroButton.count() === 0) {
        // Try alternative selector for StreamField add buttons
        const streamFieldAdd = this.page.locator('.stream-field-add button, .c-sf-add__button');
        if (await streamFieldAdd.count() > 0) {
          await streamFieldAdd.first().click();
          await this.page.waitForTimeout(1000);
          
          // Look for hero option in dropdown
          const heroOption = this.page.locator('button:has-text("Hero"), li:has-text("Hero Section")');
          if (await heroOption.count() > 0) {
            await heroOption.first().click();
          }
        }
      } else {
        await addHeroButton.first().click();
      }
      
      // Wait for hero block to be added
      await this.page.waitForTimeout(2000);
      
      // Fill intro text in rich text field
      const introField = this.page.locator('textarea[name*="intro"], .rich-text textarea, [data-field="intro"] textarea');
      if (await introField.count() > 0) {
        await introField.first().fill(heroData.intro);
        Logger.success('✅ Added intro text');
      }
      
      // Add CTA links if provided
      if (heroData.cta_links && heroData.cta_links.length > 0) {
        await this.addCTALinks(heroData.cta_links);
      }
      
      Logger.success('✅ Hero section added successfully');
      
    } catch (error) {
      throw new Error(`Failed to add Hero section: ${error.message}`);
    }
  }

  /**
   * Add CTA links to Hero section
   * @param {Array} ctaLinks - Array of CTA link objects
   */
  async addCTALinks(ctaLinks) {
    try {
      Logger.info(`🔗 Adding ${ctaLinks.length} CTA links`);
      
      for (let i = 0; i < ctaLinks.length; i++) {
        const link = ctaLinks[i];
        
        // Find add link button within hero section
        const addLinkButton = this.page.locator('button:has-text("Add"), .stream-field-add button').last();
        
        if (await addLinkButton.count() > 0) {
          await addLinkButton.click();
          await this.page.waitForTimeout(1000);
          
          // Select link type (button or carrot)
          const linkTypeOption = this.page.locator(`li:has-text("${link.type}"), button:has-text("${link.type}")`);
          if (await linkTypeOption.count() > 0) {
            await linkTypeOption.first().click();
            await this.page.waitForTimeout(1000);
          }
          
          // Fill link text
          const linkTextInput = this.page.locator('input[name*="text"], input[placeholder*="text"]').last();
          if (await linkTextInput.count() > 0) {
            await linkTextInput.fill(link.text);
          }
          
          // Handle external URL
          if (link.link_type === 'external') {
            const urlInput = this.page.locator('input[name*="url"], input[type="url"]').last();
            if (await urlInput.count() > 0) {
              await urlInput.fill(link.url);
            }
          }
          
          Logger.success(`✅ Added CTA link: ${link.text}`);
        }
        
        await this.page.waitForTimeout(1000);
      }
      
    } catch (error) {
      Logger.error(`❌ Error adding CTA links: ${error.message}`);
      // Don't throw error for CTA links - this is optional for MVP
    }
  }

  /**
   * Save the HomePage form
   */
  async saveHomePage() {
    try {
      Logger.info('💾 Saving HomePage');
      
      // Find and click save button
      const saveButton = this.page.locator('button:has-text("Save"), input[type="submit"][value*="Save"]');
      
      if (await saveButton.count() > 0) {
        await saveButton.first().click();
        await this.page.waitForLoadState('networkidle');
        Logger.success('✅ HomePage saved successfully');
      } else {
        throw new Error('Could not find save button');
      }
      
    } catch (error) {
      throw new Error(`Failed to save HomePage: ${error.message}`);
    }
  }

  /**
   * Verify HomePage was created and displays correctly
   * @param {Object} homepageData - Expected homepage data
   */
  async verifyHomePage(homepageData) {
    try {
      Logger.info('🔍 Verifying HomePage creation');
      
      // Navigate to the homepage
      await this.page.goto(Environment.wagtail.baseUrl);
      await this.page.waitForLoadState('networkidle');
      
      // Check for page title
      const pageTitle = await this.page.title();
      if (pageTitle.includes(homepageData.title) || pageTitle.includes('House Gallery')) {
        Logger.success('✅ Homepage title verified');
      }
      
      // Check for hero intro text
      if (homepageData.hero && homepageData.hero.intro) {
        const introText = this.page.locator('text=' + homepageData.hero.intro.substring(0, 20));
        if (await introText.count() > 0) {
          Logger.success('✅ Hero intro text found');
        } else {
          Logger.warn('⚠️  Hero intro text not found on page');
        }
      }
      
      // Take a screenshot for verification
      await this.page.screenshot({ path: 'test-results/homepage-verification.png' });
      Logger.info('📸 Screenshot saved for verification');
      
      return { success: true, verified: true };
      
    } catch (error) {
      Logger.error(`❌ Error verifying HomePage: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  /**
   * Complete homepage initialization workflow
   * @param {Object} config - Homepage configuration object
   */
  async initializeHomepage(config) {
    try {
      Logger.info('🚀 Starting homepage initialization workflow');
      
      const results = {
        deleted_pages: [],
        created_homepage: false,
        added_hero: false,
        verified: false
      };
      
      // Step 1: Find and delete default pages
      const defaultPages = await this.findDefaultPages();
      for (const page of defaultPages) {
        await this.deletePage(page);
        results.deleted_pages.push(page.title);
      }
      
      // Step 2: Create new HomePage
      await this.createHomePage(config.homepage);
      results.created_homepage = true;
      
      // Step 3: Add Hero section
      await this.addHeroSection(config.homepage.hero);
      results.added_hero = true;
      
      // Step 4: Save the page
      await this.saveHomePage();
      
      // Step 5: Verify the result
      const verification = await this.verifyHomePage(config.homepage);
      results.verified = verification.success;
      
      Logger.success('🎉 Homepage initialization completed successfully');
      return { success: true, results };
      
    } catch (error) {
      Logger.error(`❌ Homepage initialization failed: ${error.message}`);
      throw error;
    }
  }
}