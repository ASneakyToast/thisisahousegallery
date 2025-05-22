# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Wagtail-based (Django) implementation of "This is a House Gallery", a gallery website built with:

- Wagtail 6.3.2 (CMS)
- Django 5.0.10 (Web framework)
- PostgreSQL (Database)
- Google Cloud Platform (Hosting/Storage)
- Webpack (Frontend asset bundling)

The project follows a standard Django/Wagtail architecture with models for artists, artworks, exhibitions, and site content. It uses Docker for local development and deployment.

## Common Commands

### Local Development Setup

Start the local development environment:

```bash
# Start the local development environment with Docker
docker-compose -f compose/compose.yml up

# Create a superuser to access the admin
docker-compose -f compose/compose.yml exec django python manage.py createsuperuser
```

### Django Commands

Run these commands inside the Django container:

```bash
# Django management commands
docker-compose -f compose/compose.yml exec django python manage.py <command>

# Make and apply migrations
docker-compose -f compose/compose.yml exec django python manage.py makemigrations
docker-compose -f compose/compose.yml exec django python manage.py migrate

# Create a superuser
docker-compose -f compose/compose.yml exec django python manage.py createsuperuser

# Shell access
docker-compose -f compose/compose.yml exec django python manage.py shell
```

### Testing

```bash
# Run all tests
docker-compose -f compose/compose.yml exec django pytest

# Run specific tests
docker-compose -f compose/compose.yml exec django pytest path/to/test.py

# Run tests with coverage
docker-compose -f compose/compose.yml exec django coverage run -m pytest
docker-compose -f compose/compose.yml exec django coverage html
```

### Linting and Type Checking

```bash
# Run ruff linting
docker-compose -f compose/compose.yml exec django ruff check .

# Run mypy type checking
docker-compose -f compose/compose.yml exec django mypy housegallery

# Run djlint for template linting
docker-compose -f compose/compose.yml exec django djlint --check housegallery/templates
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
docker-compose -f compose/compose.yml down
docker volume rm housegallery_node_modules
docker-compose -f compose/compose.yml up
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