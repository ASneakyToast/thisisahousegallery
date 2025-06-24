import { test, expect } from '@playwright/test';
import { DataLoader } from '../../utils/data-loader.js';
import { ProgressTracker, BatchTracker } from '../../utils/progress-tracker.js';
import { Logger } from '../../utils/logger.js';
import { ArtistOperations } from './artist-operations.js';

/**
 * Artist Management Test Suite
 * 
 * Comprehensive test that processes artist data from test configuration:
 * - Searches for existing artists by name
 * - Creates artists if not found
 * - Updates artists if data has changed
 * - Skips artists if no changes needed
 */

test.describe('Artist Management', () => {
  let batchTracker;
  
  test.beforeAll(async () => {
    Logger.info('🎨 Starting Artist Management Test Suite');
  });

  test.afterAll(async () => {
    if (batchTracker) {
      await batchTracker.complete();
    }
    Logger.info('✅ Artist Management Test Suite completed');
  });

  test('Process all artists from test data', async ({ page }) => {
    // Load artist test data
    const artists = await DataLoader.loadArtists();
    Logger.info(`📁 Loaded ${artists.length} artists from test data`);
    
    // Initialize operations and tracking
    const artistOps = new ArtistOperations(page);
    batchTracker = ProgressTracker.createBatchTracker('artists', 1, artists.length);
    
    const results = {
      created: [],
      updated: [],
      unchanged: [],
      failed: []
    };
    
    // Process each artist
    for (let i = 0; i < artists.length; i++) {
      const artist = artists[i];
      
      Logger.info(`\n🎯 Processing artist ${i + 1}/${artists.length}: ${artist.name}`);
      Logger.progress(`Processing: ${artist.name}`, i + 1, artists.length);
      
      try {
        const result = await artistOps.processArtist(artist);
        
        // Categorize results
        switch (result.action) {
          case 'created':
            results.created.push({ artist: artist.name, ...result });
            Logger.success(`✅ Created: ${artist.name}`);
            await batchTracker.markCompleted(artist.name, { action: 'created' });
            break;
            
          case 'updated':
            results.updated.push({ 
              artist: artist.name, 
              changedFields: result.changedFields,
              ...result 
            });
            Logger.success(`🔄 Updated: ${artist.name} (${result.changedFields.join(', ')})`);
            await batchTracker.markCompleted(artist.name, { action: 'updated', changedFields: result.changedFields });
            break;
            
          case 'no_changes':
            results.unchanged.push({ artist: artist.name, ...result });
            Logger.info(`⏭️  No changes: ${artist.name}`);
            await batchTracker.markSkipped(artist.name, 'no changes needed');
            break;
            
          default:
            results.failed.push({ artist: artist.name, ...result });
            Logger.error(`❌ Failed: ${artist.name} - ${result.error}`);
            await batchTracker.markFailed(artist.name, result.error);
        }
        
        // Brief pause between operations
        await page.waitForTimeout(500);
        
      } catch (error) {
        const errorResult = {
          artist: artist.name,
          success: false,
          action: 'process_failed',
          error: error.message
        };
        
        results.failed.push(errorResult);
        Logger.error(`❌ Failed: ${artist.name} - ${error.message}`);
        await batchTracker.markFailed(artist.name, error.message);
      }
    }
    
    // Generate comprehensive report
    await generateTestReport(results, batchTracker);
    
    // Assert that we have some successful operations
    const successfulOps = results.created.length + results.updated.length + results.unchanged.length;
    expect(successfulOps).toBeGreaterThan(0);
    
    // Assert that failures are within acceptable limits (optional)
    const failureRate = results.failed.length / artists.length;
    expect(failureRate).toBeLessThanOrEqual(0.2); // 20% or fewer failures
  });

  test('Verify artist data integrity', async ({ page }) => {
    Logger.info('🔍 Verifying artist data integrity');
    
    const artists = await DataLoader.loadArtists();
    const artistOps = new ArtistOperations(page);
    
    let verificationsPassed = 0;
    let verificationsTotal = 0;
    
    for (const testArtist of artists) {
      try {
        verificationsTotal++;
        
        // Search for the artist
        const searchResult = await artistOps.searchArtist(testArtist.name);
        
        if (searchResult.found) {
          // Get detailed data
          const cmsData = await artistOps.getArtistData(searchResult.artist);
          
          // Verify key fields match
          const nameMatches = cmsData.name && 
            cmsData.name.toLowerCase() === testArtist.name.toLowerCase();
          
          if (nameMatches) {
            verificationsPassed++;
            Logger.success(`✅ Verified: ${testArtist.name}`);
          } else {
            Logger.warn(`⚠️  Name mismatch for ${testArtist.name}: ${cmsData.name}`);
          }
        } else {
          Logger.warn(`⚠️  Artist not found: ${testArtist.name}`);
        }
        
      } catch (error) {
        Logger.error(`❌ Verification failed for ${testArtist.name}: ${error.message}`);
      }
    }
    
    Logger.info(`📊 Verification Results: ${verificationsPassed}/${verificationsTotal} passed`);
    
    // Assert that most verifications passed
    const successRate = verificationsPassed / verificationsTotal;
    expect(successRate).toBeGreaterThanOrEqual(0.8); // At least 80% should pass
  });

  test('Test individual artist operations', async ({ page }) => {
    Logger.info('🧪 Testing individual artist operations');
    
    const artistOps = new ArtistOperations(page);
    
    // Test data - a simple artist
    const testArtist = {
      id: 'test_artist_001',
      name: 'Test Artist for Operations',
      bio: 'This is a test artist for operation validation.',
      website: 'https://testartist.example.com',
      birth_year: 1980
    };
    
    try {
      // Test 1: Search for non-existent artist
      Logger.info('🔍 Testing search for non-existent artist');
      const searchResult1 = await artistOps.searchArtist(testArtist.name);
      expect(searchResult1.found).toBeFalsy();
      
      // Test 2: Create artist
      Logger.info('➕ Testing artist creation');
      const createResult = await artistOps.createArtist(testArtist);
      expect(createResult.success).toBeTruthy();
      expect(createResult.action).toBe('created');
      
      // Test 3: Search for created artist
      Logger.info('🔍 Testing search for created artist');
      const searchResult2 = await artistOps.searchArtist(testArtist.name);
      expect(searchResult2.found).toBeTruthy();
      expect(searchResult2.matchType).toBe('exact');
      
      // Test 4: Update artist with changed data
      Logger.info('🔄 Testing artist update');
      const updatedTestArtist = {
        ...testArtist,
        bio: 'Updated bio for test artist.',
        birth_year: 1981
      };
      
      const updateResult = await artistOps.updateArtist(searchResult2.artist, updatedTestArtist);
      expect(updateResult.success).toBeTruthy();
      expect(updateResult.action).toBe('updated');
      expect(updateResult.changedFields).toContain('bio');
      expect(updateResult.changedFields).toContain('birth_year');
      
      // Test 5: Update artist with same data (no changes)
      Logger.info('⏭️  Testing no-change update');
      const noChangeResult = await artistOps.updateArtist(searchResult2.artist, updatedTestArtist);
      expect(noChangeResult.success).toBeTruthy();
      expect(noChangeResult.action).toBe('no_changes');
      
      Logger.success('✅ All individual operations passed');
      
    } catch (error) {
      Logger.error(`❌ Individual operations test failed: ${error.message}`);
      throw error;
    }
  });
});

/**
 * Generate comprehensive test report
 * @param {Object} results - Test results
 * @param {BatchTracker} batchTracker - Batch tracker instance
 */
async function generateTestReport(results, batchTracker) {
  Logger.info('\n' + '='.repeat(60));
  Logger.info('📊 ARTIST MANAGEMENT TEST REPORT');
  Logger.info('='.repeat(60));
  
  // Summary statistics
  const total = results.created.length + results.updated.length + 
                results.unchanged.length + results.failed.length;
  
  Logger.info(`📈 Summary Statistics:`);
  Logger.info(`   Total Artists Processed: ${total}`);
  Logger.info(`   ✅ Created: ${results.created.length}`);
  Logger.info(`   🔄 Updated: ${results.updated.length}`);
  Logger.info(`   ⏭️  Unchanged: ${results.unchanged.length}`);
  Logger.info(`   ❌ Failed: ${results.failed.length}`);
  
  const successRate = ((total - results.failed.length) / total) * 100;
  Logger.info(`   📊 Success Rate: ${successRate.toFixed(1)}%`);
  
  // Detailed breakdowns
  if (results.created.length > 0) {
    Logger.info(`\n📝 Created Artists (${results.created.length}):`);
    results.created.forEach(result => {
      Logger.info(`   • ${result.artist}`);
    });
  }
  
  if (results.updated.length > 0) {
    Logger.info(`\n🔄 Updated Artists (${results.updated.length}):`);
    results.updated.forEach(result => {
      Logger.info(`   • ${result.artist} (${result.changedFields.join(', ')})`);
    });
  }
  
  if (results.unchanged.length > 0) {
    Logger.info(`\n⏭️  Unchanged Artists (${results.unchanged.length}):`);
    results.unchanged.forEach(result => {
      Logger.info(`   • ${result.artist}`);
    });
  }
  
  if (results.failed.length > 0) {
    Logger.warn(`\n❌ Failed Operations (${results.failed.length}):`);
    results.failed.forEach(result => {
      Logger.warn(`   • ${result.artist}: ${result.error}`);
    });
  }
  
  // Save report to batch tracker
  const reportData = {
    timestamp: new Date().toISOString(),
    summary: {
      total,
      created: results.created.length,
      updated: results.updated.length,
      unchanged: results.unchanged.length,
      failed: results.failed.length,
      successRate: successRate
    },
    details: results
  };
  
  // Add report data to batch tracker
  batchTracker.reportData = reportData;
  
  Logger.info('\n' + '='.repeat(60));
  Logger.info('📁 Full report generated');
  Logger.info('='.repeat(60));
}