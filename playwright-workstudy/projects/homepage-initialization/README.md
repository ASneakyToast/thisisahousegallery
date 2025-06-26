# Homepage Initialization - Playwright Automation

## Overview

This project automates the initialization of the Wagtail CMS homepage for "This is a House Gallery". It replaces the default Wagtail welcome page with a custom HomePage featuring a Hero section with intro text and call-to-action links.

## MVP Implementation (Approach 1)

This is the **Rapid MVP** implementation focused on core functionality with basic error handling. Perfect for proof-of-concept and getting the automation working quickly.

## Project Structure

```
homepage-initialization/
├── homepage-initialization.spec.js    # Main test suite
├── homepage-operations.js             # Core operations class
├── test-data/
│   └── homepage-content.json         # Homepage configuration
└── README.md                         # This file
```

## Core Features

### ✅ Implemented
- **Default Page Deletion**: Automatically finds and removes default Wagtail welcome pages
- **Homepage Creation**: Creates new HomePage with proper title and slug
- **Hero Section**: Adds Hero StreamField block with intro text
- **CTA Links**: Adds call-to-action links (button and carrot types)
- **Verification**: Basic verification of homepage creation and content
- **Progress Logging**: Comprehensive logging throughout the workflow
- **Error Handling**: Basic error handling with descriptive failure messages

### 🎯 Test Cases
1. **Complete Workflow Test**: End-to-end homepage initialization
2. **Content Verification Test**: Validates homepage content and structure
3. **Individual Operations Test**: Tests core operations independently

## Configuration

Homepage content is configured in `test-data/homepage-content.json`:

```json
{
  "homepage": {
    "title": "This is a House Gallery",
    "slug": "home",
    "hero": {
      "intro": "serves as a project and exhibition place for close friends, local artists, writers, and curators",
      "cta_links": [
        {
          "type": "button",
          "text": "When's the next show?",
          "url": "https://www.thisisahousegallery.com/exhibitions",
          "link_type": "external"
        },
        {
          "type": "carrot", 
          "text": "Find out who lives here",
          "url": "https://www.thisisahousegallery.com/about",
          "link_type": "external"
        }
      ]
    }
  }
}
```

## Running the Tests

From the `playwright-workstudy` directory:

```bash
# Run all homepage initialization tests
npx playwright test projects/homepage-initialization/

# Run specific test
npx playwright test projects/homepage-initialization/homepage-initialization.spec.js

# Run with UI mode for debugging
npx playwright test projects/homepage-initialization/ --ui

# Run with headed browser for visual debugging
npx playwright test projects/homepage-initialization/ --headed
```

## Operations Class Methods

### Core Workflow
- `initializeHomepage(config)` - Complete initialization workflow
- `findDefaultPages()` - Search for and identify default pages
- `deletePage(pageInfo)` - Delete specified page
- `createHomePage(homepageData)` - Create new HomePage
- `addHeroSection(heroData)` - Add Hero StreamField block
- `saveHomePage()` - Save the HomePage form
- `verifyHomePage(homepageData)` - Verify creation and content

### Helper Methods
- `addCTALinks(ctaLinks)` - Add call-to-action links to Hero section

## Success Criteria

The MVP considers the test successful when:
- ✅ Default Wagtail pages are successfully deleted
- ✅ New HomePage is created with correct title and slug
- ✅ Hero section is added to the StreamField
- ✅ Basic content verification passes
- ✅ No critical errors during the workflow

## Future Enhancements (Not in MVP)

The following features are planned for future iterations:
- Advanced data comparison and validation
- Gallery block automation
- Comprehensive error recovery mechanisms
- Batch processing capabilities
- Enhanced StreamField manipulation
- Cross-browser compatibility testing
- Integration with existing utility frameworks

## Technical Notes

### StreamField Automation
The project uses multiple selector strategies for robust StreamField automation:
1. Primary: Accessibility selectors (`getByRole`, `getByLabel`)
2. Secondary: Data attributes (`data-testid`, `data-block-type`)
3. Tertiary: CSS selectors with defensive validation

### Error Handling Strategy
- Fail fast approach for critical errors
- Graceful degradation for optional features (CTA links)
- Comprehensive error logging with context
- Screenshot capture for debugging

### Dependencies
- Follows existing playwright-workstudy patterns
- Uses established Logger and CMSHelpers utilities
- Compatible with current authentication setup
- Integrates with existing progress tracking

## Debugging Tips

1. **Visual Debugging**: Use `--headed` flag to see browser interactions
2. **Screenshots**: Check `test-results/` for verification screenshots
3. **Logging**: All operations include detailed console logging
4. **Selector Issues**: The operations class uses multiple fallback selectors
5. **StreamField Problems**: Verify Wagtail admin interface hasn't changed

## Status: ✅ MVP Complete

This MVP implementation provides a solid foundation for homepage initialization automation. The code follows established patterns from the artist-management project and can be enhanced incrementally in future iterations.