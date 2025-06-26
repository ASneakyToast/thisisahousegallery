import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

/**
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './',
  testMatch: ['tests/**/*.spec.js', 'projects/**/*.spec.js'],
  
  /* Global setup to run before all tests */
  globalSetup: './config/global-setup.js',
  
  /* Run tests in files in parallel */
  fullyParallel: false, // Set to false initially for sequential processing
  
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 1,
  
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : 1, // Start with 1 worker for predictable execution
  
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html', { outputFolder: 'reports/html-report' }],
    ['json', { outputFile: 'reports/results.json' }],
    ['list']
  ],
  
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Authentication state */
    storageState: './auth/auth.json',
    
    /* Base URL for tests */
    baseURL: process.env.WAGTAIL_BASE_URL || 'http://localhost:8000',
    
    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',
    
    /* Screenshot on failure */
    screenshot: 'only-on-failure',
    
    /* Video recording */
    video: 'retain-on-failure',
    
    /* Timeouts */
    actionTimeout: 15000,
    navigationTimeout: 30000,
    
    /* Browser context options */
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'setup',
      testMatch: '**/auth.setup.js',
      teardown: 'cleanup',
    },
    {
      name: 'cleanup',
      testMatch: '**/auth.cleanup.js',
    },
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      dependencies: ['setup'],
    },
    {
      name: 'artist-management',
      testDir: './projects/artist-management',
      use: { 
        ...devices['Desktop Chrome'],
        storageState: './auth/auth.json',
        headless: false,
        slowMo: 1000,
      },
      dependencies: ['setup'],
      retries: 0,
    },
    {
      name: 'homepage-initialization',
      testDir: './projects/homepage-initialization',
      use: { 
        ...devices['Desktop Chrome'],
        storageState: './auth/auth.json',
        headless: false,
        slowMo: 1000,
      },
      dependencies: ['setup'],
      retries: 0,
    },
    // {
    //   name: 'artwork-processing',
    //   testDir: './tests/artworks',
    //   use: { ...devices['Desktop Chrome'] },
    //   dependencies: ['setup', 'artist-processing'],
    //   retries: 2,
    // }
  ],

  /* Environment-specific overrides */
  ...(process.env.NODE_ENV === 'production' && {
    use: {
      baseURL: process.env.WAGTAIL_BASE_URL,
      ignoreHTTPSErrors: false,
    },
    retries: 3,
    workers: 2,
  }),

  /* Local development overrides */
  ...(process.env.NODE_ENV === 'development' && {
    use: {
      headless: false,
      slowMo: 500,
    },
    workers: 1,
  }),
});