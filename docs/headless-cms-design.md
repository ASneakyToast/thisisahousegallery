# Headless CMS Design — This is a House Gallery

**Status:** Draft for review
**Author:** Joel + Hermes (OpenCode-orchestrated)
**Date:** 2026-08-03
**Branch source:** `docs/headless-cms-design`

---

## 1. Context & Goals

We are retiring the paid Wagtail/Cloud Run/GCP stack and replacing it with a
self-hosted, headless content platform. This is **not just a cheaper host** —
the real product is a **headless CMS that serves multiple artist frontends
pulling from one content API**. This is a House Gallery is the first (and
reference) tenant; other artists become tenants later.

### Non-goals (for now)
- No multi-tenant *onboarding/auth isolation* logic yet — only the data seam.
- No full marketing-site feature set (newsletter automation, kiosk) in v1.
- No custom admin UI — begin with SQLAdmin CRUD screens.

---

## 2. Architecture Decision

**Build a dedicated FastAPI headless CMS** (Path C), replacing both the
Wagtail admin/DB and the static-content-collections alternative.

```
 Artist #1 (you):  FastAPI Headless CMS (local, Postgres)
   your Astro site (./www) ──build-time fetch──▶ GET /v1/*
   your admin (SQLAdmin CRUD) / Swagger /docs
        │
 Artist #2..N:     same CMS, public behind Cloudflare Tunnel
   their frontends ──build-time fetch (+ optional SSE later)──▶ GET /v1/*
```

### Why FastAPI
- **Auto Swagger/OpenAPI** (`/docs`) — the self-documenting contract artists use.
- **Async-native** — SSE/multiplexing later is a clean add.
- Python home team; content models already exist in `housegallery-go`.

### What we reuse
- **Content model** from `housegallery-go` (artists, artworks, exhibitions,
  images, tags, all relationships) — ported, not redesigned.
- **Migration tool** (`housegallery-go/tools/migrate`) proof that data leaves
  Wagtail cleanly (`export.json` exists, fully normalized).
- **API-key tables** that already exist in the Wagtail DB
  (`api_apikey`, `api_readonlytoken`) map onto the future tenant auth.

---

## 3. Content Model (SQLAlchemy models)

Port from `housegallery-go`. Every content table carries a `tenant_id` FK.

```
sites / tenants        → id, slug, name, public_base_url      (seam; 1 row now)
artists                → id, tenant_id, name, slug, bio, website, email,
                         birth_year, socials, profile_image_id
artworks               → id, tenant_id, title, slug, description, size,
                         width_inches, height_inches, depth_inches, date, price
exhibitions            → id, tenant_id, title, slug, start_date, end_date,
                         description, body, video_embed_url, listing fields
images                 → id, tenant_id, title, alt, credit, description,
                         file (object key), width, height
tags                   → id, tenant_id, name, slug
relationships          → artwork_artists, artwork_images, artwork_tags,
                         exhibition_artists, exhibition_artworks,
                         exhibition_photos
navigation, site_settings, events, places
```

### Tenant seam (Q1 — day one)
- `tenant_id` FK on all content tables; nullable→defaulted to the single row.
- Public routes keyed by `site_slug` path param.
- Middleware filters every query by the resolved tenant.
- Near-zero marginal cost now; when artist #2 joins: add `sites` row, a
  per-tenant API key, and the isolation logic — no schema redesign.

---

## 4. Read API (v1, public, self-documenting)

```
GET /v1/site-settings            → nav, site title, contact, socials
GET /v1/exhibitions              → list (future/current/past)
GET /v1/exhibitions/{slug}       → detail + artworks + photos
GET /v1/artists                  → list
GET /v1/artists/{slug}           → detail + artworks
GET /v1/artworks                 → list (+ filters: artist/tag/exhibition)
GET /v1/artworks/{slug}          → detail
GET /v1/images/{id}              → meta + rendition URLs
GET /v1/tags
/docs (Swagger UI)
```

- Responses use **absolute image/rendition URLs** so a future origin swap is a
  config change, not a rewrite.
- Primary consumption = **build-time fetch** into static frontends.
- Optional later: SSE broadcast for live/kiosk content.

---

## 5. Image & Storage Strategy (Q2 — confirmed)

**Decision:** three roles, deliberately separated.

| Role | Approach |
|---|---|
| **Primary / canonical** | Local disk on this machine (`media/{tenant}/{id}/original.jpg`) — already pulled down (2.48 GB). FastAPI reads/processes from here. |
| **Active public serving** | **Cloud store (S3-compatible, e.g. R2/B2) is the public origin from the start.** Image/rendition URLs point at the bucket/CDN. Remote artists' builds fetch from the bucket, never hammering this machine. |
| **Backup / DR** | restic/rclone → cloud bucket, matching the existing Immich backup architecture. |

Renditions: pre-generate multiple sizes at ingest (reuse
`housegallery-go` imaging processor design) and store them in the same store.

**Local builds** of your own site can hit the local origin for speed; public
URLs remain bucket-based.

---

## 6. Admin (Q3 — confirmed)

- **v1:** SQLAdmin CRUD screens (FastAPI + SQLAlchemy admin package), login-gated.
- Later: a custom admin/editor UI only if the non-technical editor demands it —
  defer.

---

## 7. Operations (Hermes-managed)

- **Stack:** Docker Compose (Postgres + FastAPI + admin) on the Homelab box.
- **Migrations:** Alembic.
- **Public API:** Cloudflare Tunnel → stable URL.
- **Backups:** restic/rclone (media) + `pg_dump` (Postgres), on the established
  schedule.
- **Publish pipeline:** Hermes cron — editor edits → API → Astro build(s) →
  deploy to Netlify; health-check alerts to Discord.

---

## 8. How this reconciles with existing work

- **PR #1** (`www/`, Astro scaffold) is still the public frontend — unchanged.
- **Data layer changes:** instead of ingesting `export.json` into content
  collections, `www/` will fetch from the FastAPI CMS at build time.
  → So PR #2 becomes "wire `www/` to the CMS API," which requires the CMS built
  first.

---

## 9. Build order (suggested)

1. **CMS scaffold (PR):** FastAPI project, Postgres + Docker Compose, Alembic,
   SQLAdmin, `/docs` up.
2. **Models + migration:** port `housegallery-go` models; ingest fresh DB dump
   (`fresh-20260803-2056.sql`) + migrate images into store.
3. **Read API v1:** the `/v1/*` endpoints + Swagger + absolute URLs.
4. **Wire `www/`:** Astro build fetches from CMS → static pages.
5. **Netlify deploy + tunnel:** public site + public CMS URL.
6. **Tear down GCP** once live.

---

## 10. Decisions on open questions (2026-08-03)

### 10.1 Object store provider → **AWS S3**
- Rationale: consolidating other AWS services; one account/one mental model outweighs
  R2's egress-fee advantage for a gallery's modest media traffic.
- R2/B2 remain ~config-swap later (all S3-compatible; URLs stored absolute).
- **Full-res originals → S3 lifecycled to Glacier/Deep Archive** (cold, cheap archive).
  **Renditions → S3 Standard** (what builds/browsers fetch).

### 10.2 Rendition set → reuse existing `images.py` sizes
- `thumbnail_400`, `web_optimized_1200` (`width-1200|webp q85`), `high_quality_2400`
  (`max-2400|webp q95`) — matches template usage (width-400/800/1200/1440).
- **Full-res originals always preserved** (archive tier), never served in page.
- Hi-res cap ~2400–3840px (4K-ish); WebP everywhere.

### 10.3 Newsletter + kiosk → **decouple from CMS v1**
- **Kiosk:** a separate consumer app of the CMS API (own Astro/static app, same media),
  NOT a built-in CMS feature. Only pre-rendered as a route if TTFP/caching benefits.
- **Newsletter:** keep as a *future, separate project* (subscriber service + AWS SES is the
  natural fit). CMS v1 = content only; subscribers may be a thin stored record, but sending
  is out of scope for v1. Do NOT gate the core gallery on it.


