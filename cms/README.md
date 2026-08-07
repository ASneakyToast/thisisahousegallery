# This is a House Gallery — FastAPI Headless CMS

A self-hosted, headless content platform for
[thisisahousegallery.com](https://thisisahousegallery.com). It serves multiple
artist frontends from one content API. See the design spec at
[`../../docs/headless-cms-design.md`](../../docs/headless-cms-design.md) in the
repo root.

This is the headless CMS implementing the design spec — content models with
the multi-tenant seam and the public read-only `/v1` API.

## Getting started

### 1. Start Postgres

```bash
docker compose up -d db
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Apply migrations

```bash
uv run alembic upgrade head
```

### 4. Run the dev server

```bash
uv run uvicorn app.main:app --reload
```

- Interactive API docs (Swagger) at http://localhost:8000/docs
- SQLAdmin admin at http://localhost:8000/admin
- Health check at http://localhost:8000/healthz

## API

Public read-only v1 routes (also visible in `/docs` Swagger):

```
GET /v1/site-settings          Site title, tagline, nav, contact, socials
GET /v1/exhibitions            List of exhibitions
GET /v1/exhibitions/{slug}     Exhibition detail (artists/artworks/photos)
GET /v1/artists                List of artists
GET /v1/artists/{slug}         Artist detail (+ artworks)
GET /v1/artworks               List (optional ?artist=&tag=&exhibition= filters)
GET /v1/artworks/{slug}        Artwork detail (artists/images/tags)
GET /v1/images/{image_id}      Image detail (+ rendition URLs)
GET /v1/tags                   List of tags
```

Use `env -u PYTHONPATH uv run ...` (or the project `.venv/Scripts/python.exe`)
if your shell's `PYTHONPATH` points at another venv.

## Environment

Copy `.env.example` to `.env` and adjust as needed.
