# This is a House Gallery API

A headless CMS API for artist portfolio microsites. This API provides secure, artist-scoped access to content including artist profiles, artworks, and optimized image renditions.

## Overview

The API is built using Django REST Framework and provides:
- API key authentication with artist-scoped access
- RESTful endpoints for artists, artworks, and images
- Automatic image optimization and rendition generation
- Comprehensive filtering, searching, and pagination
- Auto-generated API documentation

## Authentication

All API endpoints require authentication using an API key. Include your API key in the request headers:

```
API-Key: your-api-key-here
```

Or in the Authorization header:

```
Authorization: API-Key your-api-key-here
```

## Base URL

```
https://yourdomain.com/api/v1/
```

## Core Endpoints

### Artist Profile

Get the authenticated artist's profile:

```
GET /api/v1/artists/profile/
```

Response:
```json
{
  "id": 123,
  "name": "Artist Name",
  "bio": "Artist biography...",
  "website": "https://artist-site.com",
  "birth_year": 1980,
  "profile_image": {
    "id": 456,
    "title": "Profile Photo",
    "renditions": {
      "thumbnail": "https://storage.googleapis.com/...",
      "web_optimized": "https://storage.googleapis.com/...",
      "high_quality": "https://storage.googleapis.com/..."
    }
  },
  "social_media_links": [
    {
      "platform": "instagram",
      "url": "https://instagram.com/artist",
      "handle": "artist"
    }
  ],
  "metadata": {
    "artwork_count": 42
  }
}
```

### Artworks

List all artworks for the authenticated artist:

```
GET /api/v1/artworks/
```

Query parameters:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `search`: Search in title and description
- `ordering`: Sort by field (options: date, -date, id, -id)
- `materials`: Filter by materials (comma-separated)
- `year`: Filter by creation year
- `date_from`: Filter by date range start
- `date_to`: Filter by date range end

### Artwork Detail

Get detailed information about a specific artwork:

```
GET /api/v1/artworks/{id}/
```

### Featured Artworks

Get featured artworks (returns up to 6 most recent):

```
GET /api/v1/artworks/featured/
```

### Available Materials

Get all unique materials/tags used by the artist:

```
GET /api/v1/artworks/materials/
```

### Images

List all images belonging to the artist's artworks:

```
GET /api/v1/images/
```

### Image Renditions

Get all available renditions for an image:

```
GET /api/v1/images/{id}/renditions/
```

Response includes URLs for various sizes:
- `thumbnail_400`: 400px width WebP
- `web_optimized_1200`: 1200px width WebP
- `high_quality_2400`: 2400px max dimension WebP

### Custom Rendition

Generate a custom image rendition on-demand:

```
POST /api/v1/images/{id}/custom_rendition/
```

Request body:
```json
{
  "width": 800,
  "height": 600,
  "format": "webp",
  "quality": 85
}
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI Schema: `/api/schema/`

## Rate Limiting

Each API key has a configurable rate limit (default: 1000 requests/hour). Rate limit information is included in response headers:
- `X-RateLimit-Limit`: Maximum requests per hour
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets

## Error Responses

The API uses standard HTTP status codes:
- `200 OK`: Successful request
- `401 Unauthorized`: Invalid or missing API key
- `403 Forbidden`: Access denied to resource
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "detail": "Error message here"
}
```

## Integration Example (JavaScript)

```javascript
class GalleryAPI {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.baseUrl = 'https://yourdomain.com/api/v1';
  }
  
  async request(endpoint, options = {}) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      headers: {
        'API-Key': this.apiKey,
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    
    return response.json();
  }
  
  async getArtistProfile() {
    return this.request('/artists/profile/');
  }
  
  async getArtworks(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/artworks/${queryString ? '?' + queryString : ''}`);
  }
}

// Usage
const api = new GalleryAPI('your-api-key');
const artist = await api.getArtistProfile();
const artworks = await api.getArtworks({ page_size: 12 });
```

## Creating API Keys

API keys can be created through:
1. Django admin interface at `/admin/api/apikey/`
2. Management command: `python manage.py create_api_key "Artist Name"`

## Security Considerations

- API keys should be kept secure and not exposed in client-side code
- Use environment variables to store API keys
- Consider IP whitelisting for additional security
- Rotate API keys periodically
- Monitor API usage for suspicious activity