# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<!-- Migration to us-west1: Testing new dev trigger -->

## Project Overview

This is a Wagtail-based (Django) implementation of "This is a House Gallery", a gallery website built with:

- Wagtail 6.3.2 (CMS)
- Django 5.0.10 (Web framework)
- PostgreSQL (Database)
- Google Cloud Platform (Hosting/Storage)
- Webpack (Frontend asset bundling)

The project follows a standard Django/Wagtail architecture with models for artists, artworks, exhibitions, and site content. It uses Docker for local development and deployment.

## Common Commands

### Database Development Modes

The project supports two distinct development modes with clear separation:

#### Mode 1: Local Offline Development
Pure local development with PostgreSQL container - no GCP dependencies.
Perfect for offline work and most development tasks.

```bash
# Start local offline environment
docker-compose -f compose/compose.local-offline.yml up

# Create a superuser
docker-compose -f compose/compose.local-offline.yml exec django python manage.py createsuperuser

# Run migrations
docker-compose -f compose/compose.local-offline.yml exec django python manage.py migrate
```

#### Mode 2: Local Cloud Development
Connect to Cloud SQL via proxy for testing cloud features and data.
Requires GCP authentication and internet connection.

```bash
# Ensure gcloud authentication
gcloud auth application-default login

# Start local cloud environment
docker-compose -f compose/compose.local-cloud.yml up

# Run migrations against cloud database
docker-compose -f compose/compose.local-cloud.yml exec django python manage.py migrate

# Create superuser (if needed)
docker-compose -f compose/compose.local-cloud.yml exec django python manage.py createsuperuser
```

#### Mode 3: Production (GCP Secret Manager)
Production deployment uses GCP Secret Manager for all configuration - no local env files needed.

### Django Commands

Run these commands inside the Django container. Replace `<compose-file>` with either `compose.local-offline.yml` or `compose.local-cloud.yml`:

```bash
# Django management commands
docker-compose -f compose/<compose-file> exec django python manage.py <command>

# Make and apply migrations
docker-compose -f compose/<compose-file> exec django python manage.py makemigrations
docker-compose -f compose/<compose-file> exec django python manage.py migrate

# Create a superuser
docker-compose -f compose/<compose-file> exec django python manage.py createsuperuser

# Shell access
docker-compose -f compose/<compose-file> exec django python manage.py shell
```

### Testing

```bash
# Run all tests (use local-offline for most testing)
docker-compose -f compose/compose.local-offline.yml exec django pytest

# Run specific tests
docker-compose -f compose/<compose-file> exec django pytest path/to/test.py

# Run tests with coverage
docker-compose -f compose/<compose-file> exec django coverage run -m pytest
docker-compose -f compose/<compose-file> exec django coverage html
```

### Linting and Type Checking

```bash
# Run ruff linting
docker-compose -f compose/<compose-file> exec django ruff check .

# Run mypy type checking
docker-compose -f compose/<compose-file> exec django mypy housegallery

# Run djlint for template linting
docker-compose -f compose/<compose-file> exec django djlint --check housegallery/templates
```

### Frontend Development

```bash
# Run webpack dev server (auto-runs in Docker)
npm run dev

# Build frontend assets for production
npm run build

# When installing new npm packages
# Remove only the node_modules volume to allow Docker to download new packages
# This preserves the database volume
docker-compose -f compose/compose.local-offline.yml down
docker volume rm housegallery_local_node_modules
docker-compose -f compose/compose.local-offline.yml up
```

## Architecture

### Key Components

1. **Wagtail CMS**: The project is built on Wagtail for managing website content.
   - Custom page types in `housegallery/home/`, `housegallery/exhibitions/`, etc.
   - StreamFields for flexible content creation
   - Custom image model in `housegallery/images/`

2. **Django Apps**:
   - **artists**: Models for gallery artists
   - **artworks**: Models for artwork listings
   - **core**: Common functionality, blocks, and mixins
   - **exhibitions**: Exhibition pages and related models
   - **home**: Homepage and main site settings
   - **images**: Custom image model extensions

3. **Configuration**:
   - Settings separated into base, local, production, and test
   - Google Cloud integration for storage, secrets, and deployment
   - Docker-based development environment

4. **Frontend**:
   - Webpack for bundling JS and CSS
   - Custom templates in `housegallery/templates/`
   - Component-based CSS structure
   - Two static directories:
     - `/housegallery/static/` - Source files to edit
     - `/static/` - Compiled output (do not edit directly)

### Database

- PostgreSQL in development (via Docker)
- Cloud SQL in production
- Local development can toggle between local Postgres or Cloud SQL via proxy

### Deployment

- Google Cloud Run for hosting
- Google Cloud Storage for media and static files
- Continuous deployment via Cloud Build

### Google Cloud CLI (gcloud) Usage

**Important:** This project uses a hybrid architecture across regions. Always specify the correct region flag:

```bash
# Cloud Build triggers and builds (us-west2)
gcloud builds triggers list --region=us-west2
gcloud builds list --region=us-west2
gcloud builds describe [BUILD_ID] --region=us-west2

# Cloud Run services and jobs (us-west1 for dev/staging)
gcloud run services list --region=us-west1
gcloud run jobs list --region=us-west1

# Cloud SQL database (us-west2)
gcloud sql instances list  # Shows all regions
```

**Hybrid Architecture:** 
- **Cloud Build & Database**: us-west2 (triggers, builds, PostgreSQL)
- **Cloud Run Services**: us-west1 (enables custom domain mapping)
- **Custom Domains**: qa.thisisahousegallery.com → us-west1 service

### Production Deployment

**Cloud Build Triggers:**
- `housegallery-dev-jrl`: Auto-deploys dev environment on `jrl/*` branch pushes
- `housegallery-dev-tag-build`: Auto-deploys dev environment on `dev-*` tag pushes
- `housegallery-prod`: Auto-builds production on `main` branch pushes (includes database backup)
- `housegallery-prod-deploy-manual`: Manual production deployment trigger
- `housegallery-qa-sync`: Manual QA sync from production database and media

**Production Workflow:**
1. **Merge to main** → Triggers `housegallery-prod` build (backup + build image)
2. **Manual deployment** → Run `housegallery-prod-deploy-manual` trigger when ready
3. **Services created:** `housegallery-prod-service` and associated management jobs

**Production Services:**
- Main service: `housegallery-prod-service`
- Database: `housegallery-prod` (on same Cloud SQL instance)
- Jobs: `housegallery-prod-mgmt-cmd-*` (migrate, clearsessions, update-index, publish-scheduled-pages)

**Manual Production Deployment:**
```bash
# Trigger production deployment manually
gcloud builds triggers run housegallery-prod-deploy-manual --region=us-west2 --branch=main
```

**QA Environment Sync:**
To sync the QA environment with production data (database and media files):

```bash
# Sync QA environment with production data
gcloud builds triggers run housegallery-qa-sync --region=us-west2 --branch=main
```

This will:
1. Copy all media and static files from `gs://housegallery-prod` to `gs://housegallery-qa`
2. Export the latest production database backup and import it to the QA database
3. Run migrations on the QA database
4. Update the search index for the QA environment

**Note:** This operation will completely replace the QA database with production data. Ensure any QA-specific data is backed up if needed.

### Development Deployment Options

The project supports two methods for deploying to the development environment:

#### Method 1: Branch-Based Deployment (Automatic)
Push to any `jrl/*` branch to trigger automatic deployment:
```bash
git checkout -b jrl/my-feature
git push origin jrl/my-feature
# Automatically triggers housegallery-dev-jrl build
```

#### Method 2: Tag-Based Deployment (On-Demand)
Create and push a `dev-*` tag for on-demand deployment:
```bash
# Deploy current commit to dev environment
git tag dev-feature-admin-upgrades
git push origin dev-feature-admin-upgrades

# Deploy with date for testing
git tag dev-$(date +%Y%m%d)
git push origin dev-$(date +%Y%m%d)

# Deploy specific version for testing
git tag dev-v1.0.0
git push origin dev-v1.0.0
```

**Tag Naming Conventions:**
- `dev-*`: General development deployments
- `dev-feature-*`: Feature testing (e.g., `dev-feature-api-enhancement`)
- `dev-v*`: Version-specific dev deployments (e.g., `dev-v1.0.0`)
- `dev-YYYYMMDD`: Date-based deployments for testing

Both deployment methods work simultaneously and deploy to the same dev environment.

## Working with the Codebase

### Adding New Features

1. For Wagtail-specific changes:
   - New page types should extend existing base classes
   - Use StreamFields for flexible content
   - Create corresponding templates in `housegallery/templates/`

2. For frontend changes:
   - CSS components are in `housegallery/static/css/components/`
   - JS is in `housegallery/static/js/`
   - Only edit files in the `housegallery/static/` directory, not in the root `/static/` directory
   - Use the webpack dev server for hot reloading

3. For database changes:
   - Create models in the appropriate app
   - Run migrations
   - Register models with Wagtail admin if needed
   - When using StreamField, don't use the `use_json_field=True` parameter as it's already the default in Wagtail 6.x

## Libraries and Dependencies

### anime.js 4.0
The project uses anime.js v4.0, which has a modular, ESM-first architecture with named exports:

```javascript
// Correct import pattern for anime.js v4.0
import { animate, createTimeline, stagger } from 'animejs';

// Example usage
const timeline = createTimeline({
  easing: 'easeOutExpo',
  duration: 700
});

timeline.add({
  targets: element,
  translateX: ['100%', '0%'],
  opacity: [0, 1],
  duration: 600
});

// Using stagger
timeline.add({
  targets: elements,
  translateY: [20, 0],
  opacity: [0, 1],
  delay: stagger(80),
  duration: 800
});
```

Key named exports in anime.js 4.0:
- `animate` - Main animation function
- `createTimeline` - Creates a timeline to synchronize multiple animations
- `stagger` - Creates staggered animations
- `createDraggable` - Creates draggable elements
- And many other utility functions

#### Timeline Animation Syntax
In anime.js 4.0, the correct syntax for adding animations to a timeline has changed:

```javascript
// CORRECT: Pass the target element as the first argument, and animation properties as the second
timeline.add(targetElement, {
  translateX: ['100%', '0%'],
  opacity: [0, 1],
  duration: 600
});

// INCORRECT: Using targets property inside the configuration object (old v3 syntax)
timeline.add({
  targets: targetElement,
  translateX: ['100%', '0%'],
  opacity: [0, 1],
  duration: 600
});
```

This is a significant change from anime.js v3, where the targets were specified as a property in the configuration object.

## Claude Code Behavioral Patterns

### MCP Server Configuration
**Important**: Claude Code MCP servers are configured **per repository**, unlike Claude Desktop which has global MCP configuration.

- Use `claude mcp list` to see MCP servers configured for the current repository
- Use `claude mcp add <server-command>` to add MCP servers to the current repository
- MCP servers configured in one repository are not available in other repositories
- This is different from Claude Desktop where MCP servers are configured globally

### Solution Drift Prevention
**Pattern**: Continuing to troubleshoot or suggest additional fixes after a viable solution has already been identified and implemented.

**Recognition**: When the user and Claude have:
1. Identified a specific problem
2. Found and implemented a targeted solution
3. Verified the solution addresses the root cause

**Prevention**: After implementing a solution, explicitly check if the problem is resolved before suggesting additional fixes. Ask the user to test the implemented solution first.

**Example**: If we fix a database authentication error by correcting the service account configuration, don't immediately suggest password resets or other unrelated fixes without first confirming the auth issue persists.