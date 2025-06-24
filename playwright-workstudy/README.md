# Playwright CMS Automation

A comprehensive Playwright Test framework for automating Wagtail CMS content management, specifically designed for batch processing of artists and artworks in the House Gallery project.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ 
- Docker (for Wagtail development environment)
- Wagtail CMS running locally or accessible via URL

### Installation

1. **Navigate to the automation directory:**
   ```bash
   cd playwright-workstudy
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Install Playwright browsers:**
   ```bash
   npm run install:browsers
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Wagtail instance details
   ```

### First Run

1. **Start your Wagtail development environment:**
   ```bash
   # From project root - choose your development mode
   docker-compose -f compose/compose.local-offline.yml up
   ```

2. **Test authentication:**
   ```bash
   npm run test -- tests/auth.setup.js
   ```

3. **Validate data:**
   ```bash
   node -e "
   import('./utils/data-loader.js').then(({ DataLoader }) => {
     DataLoader.validateData().then(result => {
       console.log('Data validation:', result);
     });
   });
   "
   ```

## 📁 Project Structure

```
playwright-workstudy/
├── config/
│   ├── environment.js          # Environment configuration management
│   └── global-setup.js         # Global authentication setup
├── data/
│   ├── schema/                 # JSON schemas for data validation
│   │   ├── artist.schema.json
│   │   └── artwork.schema.json
│   ├── artists.json           # Sample artist data
│   └── artworks.json          # Sample artwork data
├── utils/
│   ├── data-loader.js         # Data loading and batch management
│   ├── cms-helpers.js         # Wagtail CMS interaction helpers
│   ├── logger.js              # Logging utilities
│   └── progress-tracker.js    # Progress tracking and monitoring
├── tests/
│   ├── auth.setup.js          # Authentication setup tests
│   └── auth.cleanup.js        # Authentication cleanup
├── auth/                      # Authentication state storage
├── reports/                   # Test reports and progress tracking
├── playwright.config.js       # Main Playwright configuration
├── package.json
└── README.md
```

## ⚙️ Configuration

### Environment Variables

Edit `.env` to configure your setup:

```bash
# Wagtail CMS Configuration
WAGTAIL_BASE_URL=http://localhost:8000
WAGTAIL_ADMIN_URL=/admin/
WAGTAIL_USER=admin
WAGTAIL_PASS=password

# Development Mode
DEV_MODE=local-offline  # or local-cloud, production

# Batch Processing
DEFAULT_BATCH_SIZE=20
MAX_RETRIES=3
RETRY_DELAY=2000

# Logging
LOG_LEVEL=info
ENABLE_PROGRESS_TRACKING=true

# Browser Settings
HEADLESS=true
SLOW_MO=0
BROWSER_TIMEOUT=30000
```

### Wagtail Development Modes

The automation supports all House Gallery development modes:

- **local-offline**: Pure local development with PostgreSQL container
- **local-cloud**: Connect to Cloud SQL via proxy
- **production**: Production environment (use with caution)

## 📊 Data Management

### Data Structure

The system uses JSON files matching your Wagtail models:

**Artists** (`data/artists.json`):
```json
{
  "id": "artist_001",
  "name": "Vincent van Gogh",
  "bio": "Dutch Post-Impressionist painter...",
  "website": "https://www.vangoghmuseum.nl",
  "birth_year": 1853,
  "social_media_links": [...]
}
```

**Artworks** (`data/artworks.json`):
```json
{
  "id": "artwork_001",
  "title": "The Starry Night",
  "artist_id": "artist_001",
  "description": "A masterpiece depicting...",
  "materials": ["Oil", "Canvas"],
  "size": "73.7 cm × 92.1 cm",
  "date": "1889-06-01T00:00:00Z",
  "artifacts": [...]
}
```

### Data Validation

Validate your data before processing:

```bash
node -e "
import('./utils/data-loader.js').then(({ DataLoader }) => {
  DataLoader.validateData().then(console.log);
});
"
```

### Batch Management

Data is processed in configurable batches:

```javascript
// Get a specific batch
const batch1Artists = await DataLoader.getArtistBatch(1, 20);

// Get data summary
const summary = await DataLoader.getDataSummary();
```

## 🛠️ Core Utilities

### DataLoader

Manages loading and batch processing of artist/artwork data:

```javascript
import { DataLoader } from './utils/data-loader.js';

// Load all artists
const artists = await DataLoader.loadArtists();

// Load specific batch
const batch = await DataLoader.getArtistBatch(1, 20);

// Get artist by ID
const artist = await DataLoader.getArtistById('artist_001');

// Validate data integrity
const validation = await DataLoader.validateData();
```

### CMSHelpers

Provides Wagtail-specific automation functions:

```javascript
import { CMSHelpers } from './utils/cms-helpers.js';

// Check if content exists (idempotent)
const exists = await CMSHelpers.checkArtistExists(page, 'Van Gogh');

// Create new content
await CMSHelpers.createArtist(page, artistData);
await CMSHelpers.createArtwork(page, artworkData, artistData);

// Ensure dependencies exist
await CMSHelpers.ensureArtistExists(page, artistData);

// Retry failed operations
await CMSHelpers.withRetry(() => someOperation(), 3, 2000);
```

### Logger

Comprehensive logging with colored output:

```javascript
import { Logger } from './utils/logger.js';

Logger.info('Starting batch processing');
Logger.success('Artist created successfully');
Logger.warn('Artist already exists, skipping');
Logger.error('Failed to create artwork', error);
Logger.progress('Processing items', 5, 20);
```

### ProgressTracker

Track and resume batch operations:

```javascript
import { ProgressTracker, BatchTracker } from './utils/progress-tracker.js';

// Create batch tracker
const tracker = ProgressTracker.createBatchTracker('artists', 1, 20);

// Track individual items
await tracker.markCompleted('artist_001');
await tracker.markSkipped('artist_002', 'Already exists');
await tracker.markFailed('artist_003', 'Network error');

// Complete batch
await tracker.complete();

// Get progress summary
const summary = await ProgressTracker.getProgressSummary();
```

## 🔐 Authentication

The system automatically handles Wagtail admin authentication:

1. **Global Setup**: Runs before all tests, logs into Wagtail admin
2. **State Persistence**: Saves authentication cookies to `auth/auth.json`
3. **Automatic Retry**: Handles session expiration and re-authentication

## 📝 Creating Your First Test

Here's a simple example of how to create a basic test:

```javascript
// tests/sample-artist-test.spec.js
import { test, expect } from '@playwright/test';
import { DataLoader } from '../utils/data-loader.js';
import { CMSHelpers } from '../utils/cms-helpers.js';
import { Logger } from '../utils/logger.js';

test.describe('Artist Processing', () => {
  test('Create sample artists', async ({ page }) => {
    // Load first 5 artists
    const artists = await DataLoader.loadArtists(0, 5);
    
    for (const artist of artists) {
      await test.step(`Processing artist: ${artist.name}`, async () => {
        // Check if artist already exists
        const exists = await CMSHelpers.checkArtistExists(page, artist.name);
        
        if (exists) {
          Logger.skip(`Artist already exists: ${artist.name}`);
          return;
        }
        
        // Create new artist
        await CMSHelpers.createArtist(page, artist);
        Logger.success(`Created artist: ${artist.name}`);
      });
    }
  });
});
```

Run your test:
```bash
npm test -- tests/sample-artist-test.spec.js
```

## 🚦 Available Scripts

```bash
# Run all tests
npm test

# Run with UI mode (interactive)
npm run test:ui

# Run in headed mode (see browser)
npm run test:headed

# Debug mode
npm run test:debug

# Install browsers
npm run install:browsers

# View HTML report
npm run report
```

## 🔍 Debugging

### Common Issues

1. **Authentication Failures**:
   ```bash
   # Test authentication separately
   npm test -- tests/auth.setup.js --headed
   ```

2. **Element Not Found**:
   ```bash
   # Run in headed mode to see the interface
   npm run test:headed
   ```

3. **Timeout Issues**:
   ```bash
   # Increase timeouts in .env
   BROWSER_TIMEOUT=60000
   ```

### Debug Mode

Run tests in debug mode to step through execution:

```bash
npm run test:debug
```

### Logging Levels

Adjust logging verbosity:

```bash
# .env
LOG_LEVEL=debug  # error, warn, info, debug
```

## 📊 Monitoring & Reports

### Progress Tracking

Monitor batch processing progress:

```javascript
// Get current progress summary
const summary = await ProgressTracker.getProgressSummary();
console.log(summary);
```

### HTML Reports

View detailed test reports:

```bash
npm run report
```

Reports include:
- Test execution results
- Screenshots of failures
- Detailed timing information
- Error messages and stack traces

## 🔄 Integration with House Gallery Development

### Docker Integration

The automation works with your existing Docker setup:

```bash
# Start your preferred development environment
docker-compose -f compose/compose.local-offline.yml up

# Then run automation
cd playwright-workstudy
npm test
```

### Data Sources

- Replace sample data in `data/` directory with your actual content
- Ensure data follows the JSON schemas in `data/schema/`
- Use data validation before processing large batches

## 🎯 Next Steps

With the foundational infrastructure complete, you can now:

1. **Create specific test suites** for your content types
2. **Add complex StreamField handling** for artifacts and social media
3. **Implement parallel processing** for large datasets
4. **Add custom validation rules** for your content
5. **Create monitoring dashboards** for production use

## 📚 Additional Resources

- [Playwright Documentation](https://playwright.dev/)
- [Wagtail Admin API](https://docs.wagtail.org/)
- [House Gallery Development Guide](../CLAUDE.md)

## 🐛 Troubleshooting

If you encounter issues:

1. Check the logs in `reports/` directory
2. Verify your Wagtail instance is accessible
3. Ensure authentication credentials are correct
4. Review the HTML test report for detailed error information

For complex issues, run tests in headed mode to observe the browser interactions.