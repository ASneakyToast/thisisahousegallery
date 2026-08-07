# This is a House Gallery — FastAPI Headless CMS

A self-hosted, headless content platform for
[thisisahousegallery.com](https://thisisahousegallery.com). It serves multiple
artist frontends from one content API. See the design spec at
[`../../docs/headless-cms-design.md`](../../docs/headless-cms-design.md) in the
repo root.

This is the skeleton stage only — content models and the `/v1` API are not yet
implemented.

## Getting started

### 1. Start Postgres

```bash
docker compose up -d db
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Run the dev server

```bash
uv run uvicorn app.main:app --reload
```

- Interactive API docs (Swagger) at http://localhost:8000/docs
- SQLAdmin admin at http://localhost:8000/admin
- Health check at http://localhost:8000/healthz

## Environment

Copy `.env.example` to `.env` and adjust as needed.
