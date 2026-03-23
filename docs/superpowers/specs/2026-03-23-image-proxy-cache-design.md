# Image Proxy Cache Design

## Overview

Refactor the poster image proxy from an in-memory cache buried in the folder router into a proper disk-backed image cache with its own router, higher limits, and maintenance controls.

Closes #38 (stale OMDb poster URLs return 404).

## Current State

- Proxy lives in `backend/routers/folder.py` at `GET /api/jobs/folder/poster-proxy`
- In-memory dict cache, 100 images max, FIFO eviction, lost on restart
- `Cache-Control: max-age=86400` (1 day)
- SSRF allowlist: 5 CDN hosts
- Frontend `posterSrc()` utility routes all external poster URLs through proxy
- All 9 components already use `posterSrc()`

## Design

### 1. New Images Router

**File:** `backend/routers/images.py`

**Route:** `GET /api/images/proxy?url=<encoded>`

Move the proxy logic out of folder.py into a dedicated router. Replace the old route in folder.py with a 301 redirect to the new URL for backward compatibility. Update `posterSrc()` to use the new URL.

Register in `backend/main.py`.

### 2. Disk-Backed Cache Service

**File:** `backend/services/image_cache.py`

Cache directory: configurable via `ARM_UI_IMAGE_CACHE_PATH` env var, defaults to `/data/cache/images`. Created on startup if it doesn't exist.

**Storage format:**
- `<sha256-of-url>.img` — raw image bytes
- `<sha256-of-url>.json` — metadata: `{"url": "...", "content_type": "image/jpeg", "cached_at": 1711234567.0, "accessed_at": 1711234567.0, "size": 45231}`

**In-memory index:** Dict mapping URL -> `{filename, content_type, accessed_at, size}` for fast lookups without disk reads on every request. Built on startup by scanning the cache directory.

**Limits:**
- Max entries: 1000
- Max single image: 2 MB (reject larger with 502)
- TTL: 7 days
- Eviction: LRU by `accessed_at` — evict oldest-accessed when full

**Cache-Control header:** `public, max-age=604800` (7 days)

**On startup:** Scan cache dir, load metadata files, discard entries older than TTL, rebuild in-memory index. If a `.json` metadata file exists but its `.img` file is missing, treat as orphaned — delete the metadata and skip.

**Concurrency note:** The in-memory index dict is safe under asyncio's cooperative multitasking. If threaded access is ever needed, protect with an `asyncio.Lock`.

### 3. SSRF Allowlist

No changes — keep existing 5 hosts:
- `m.media-amazon.com`
- `image.tmdb.org`
- `images-na.ssl-images-amazon.com`
- `coverartarchive.org`
- `ia.media-imdb.com`

### 4. Cache Management Endpoints

**File:** `backend/routers/maintenance.py` (extend existing)

#### `GET /api/maintenance/image-cache-stats`
Returns: `{"count": 42, "size_bytes": 2145678, "size_mb": 2.0, "oldest": "2026-03-16T12:00:00Z", "path": "/data/cache/images"}`

#### `POST /api/maintenance/clear-image-cache`
Deletes all cached files, resets in-memory index.
Returns: `{"success": true, "cleared": 42, "freed_bytes": 2145678}`

### 5. Frontend Changes

**File:** `frontend/src/lib/utils/poster.ts`

Update proxy URL from `/api/jobs/folder/poster-proxy?url=` to `/api/images/proxy?url=`.

**File:** `frontend/src/routes/maintenance/+page.svelte`

Add "Image Cache" section showing stats and a "Clear Cache" button.

### 6. Docker & Environment

All compose files and env examples in ARM-neu need the image cache volume and env var.

**Compose files (ARM-neu):**
- `docker-compose.yml` — add volume mount to `arm-ui` service
- `docker-compose.remote-transcoder.yml` — add volume mount to `arm-ui` service
- `docker-compose.dev.yml` — add dev volume mount (`./dev-data/cache/images:/data/cache/images:rw`)

Volume mount: `image-cache:/data/cache/images:rw` (named volume, persists across recreates)

Add to volumes section: `image-cache:`

**Env vars to arm-ui service:**
- `ARM_UI_IMAGE_CACHE_PATH=/data/cache/images`

**Env example files (ARM-neu):**
- `.env.example` — add `# IMAGE_CACHE_PATH=./data/image-cache` comment
- `.env.remote-transcoder.example` — same

**UI compose file:**
- `docker-compose.yml` (in automatic-ripping-machine-ui) — add volume mount for standalone dev use

### 7. Config

**File:** `backend/config.py`

Add `image_cache_path: str` field, read from `ARM_UI_IMAGE_CACHE_PATH` env var, default `/data/cache/images`.

## Testing

### Backend
- `tests/routers/test_images.py` — proxy success, SSRF rejection, cache hit, max size rejection
- `tests/services/test_image_cache.py` — store/retrieve, LRU eviction, TTL expiry, startup rebuild, clear
- `tests/routers/test_maintenance.py` — cache stats, clear endpoint (extend existing)

### Frontend
- Update `poster.test.ts` to use new URL
- Maintenance page test for cache section
