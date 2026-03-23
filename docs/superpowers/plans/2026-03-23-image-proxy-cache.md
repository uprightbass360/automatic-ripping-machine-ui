# Image Proxy Cache Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the in-memory poster proxy with a disk-backed, LRU-evicting image cache behind a dedicated router, with maintenance controls.

**Architecture:** New `image_cache.py` service handles disk I/O and in-memory index. New `images.py` router serves the proxy endpoint. Maintenance router gets cache stats and clear endpoints. Frontend updates are minimal — one URL change and one new maintenance section.

**Tech Stack:** Python/FastAPI, httpx, sha256 hashing, JSON sidecar files, SvelteKit frontend

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `backend/services/image_cache.py` | Disk-backed cache: store, retrieve, evict, clear, stats, startup scan |
| Create | `backend/routers/images.py` | `GET /api/images/proxy` — SSRF validation + cache lookup/store |
| Create | `tests/services/test_image_cache.py` | Unit tests for cache service |
| Create | `tests/routers/test_images.py` | Router tests for proxy endpoint |
| Modify | `backend/routers/maintenance.py` | Add cache stats + clear endpoints |
| Modify | `backend/routers/folder.py` | Replace old proxy with 301 redirect |
| Modify | `backend/config.py` | Add `image_cache_path` setting |
| Modify | `backend/main.py` | Register images router, init cache on startup |
| Modify | `frontend/src/lib/utils/poster.ts` | Update proxy URL |
| Modify | `frontend/src/lib/__tests__/poster.test.ts` | Update expected URLs |
| Modify | `frontend/src/lib/api/maintenance.ts` | Add cache stats + clear API functions |
| Modify | `frontend/src/routes/maintenance/+page.svelte` | Add cache section to UI |
| Modify | `tests/routers/test_maintenance.py` | Add cache endpoint tests |
| Modify | `docker-compose.yml` (UI repo) | Add cache volume |
| Modify | `docker-compose.yml` (ARM-neu) | Add cache volume + env var |
| Modify | `docker-compose.remote-transcoder.yml` (ARM-neu) | Add cache volume + env var |
| Modify | `docker-compose.dev.yml` (ARM-neu) | Add dev cache volume |

---

## Chunk 1: Cache Service

### Task 1: Config Setting

**Files:**
- Modify: `backend/config.py`

- [ ] **Step 1: Add image_cache_path to Settings**

```python
# In backend/config.py, add after arm_themes_path:
    image_cache_path: str = "/data/cache/images"
```

- [ ] **Step 2: Commit**

```bash
git add backend/config.py
git commit -m "feat: add image_cache_path config setting"
```

### Task 2: Image Cache Service — Core

**Files:**
- Create: `backend/services/image_cache.py`
- Create: `tests/services/test_image_cache.py`

- [ ] **Step 1: Write tests for cache service**

```python
# tests/services/test_image_cache.py
"""Tests for backend.services.image_cache — disk-backed image cache."""

from __future__ import annotations

import json
import time

import pytest

from backend.services import image_cache


@pytest.fixture
def cache_dir(tmp_path):
    """Provide a temp cache dir and reset the service."""
    d = tmp_path / "images"
    d.mkdir()
    image_cache._index.clear()
    image_cache._cache_dir = str(d)
    return d


def test_store_and_retrieve(cache_dir):
    """Stored image can be retrieved."""
    url = "https://m.media-amazon.com/images/test.jpg"
    data = b"\xff\xd8\xff\xe0fake-jpeg"
    image_cache.store(url, data, "image/jpeg")
    result = image_cache.retrieve(url)
    assert result is not None
    content, content_type = result
    assert content == data
    assert content_type == "image/jpeg"


def test_retrieve_miss(cache_dir):
    """Missing URL returns None."""
    assert image_cache.retrieve("https://example.com/nope.jpg") is None


def test_eviction_lru(cache_dir):
    """When cache exceeds max entries, LRU entry is evicted."""
    old_max = image_cache._MAX_ENTRIES
    image_cache._MAX_ENTRIES = 3
    try:
        for i in range(4):
            image_cache.store(f"https://example.com/{i}.jpg", b"img", "image/jpeg")
        # Entry 0 should be evicted
        assert image_cache.retrieve("https://example.com/0.jpg") is None
        assert image_cache.retrieve("https://example.com/3.jpg") is not None
    finally:
        image_cache._MAX_ENTRIES = old_max


def test_ttl_expiry(cache_dir):
    """Expired entries are not returned."""
    url = "https://example.com/old.jpg"
    image_cache.store(url, b"img", "image/jpeg")
    # Backdate the entry
    filename = image_cache._url_to_filename(url)
    meta_path = cache_dir / f"{filename}.json"
    meta = json.loads(meta_path.read_text())
    meta["cached_at"] = time.time() - image_cache._TTL_SECONDS - 1
    meta["accessed_at"] = meta["cached_at"]
    meta_path.write_text(json.dumps(meta))
    image_cache._index[url]["cached_at"] = meta["cached_at"]
    assert image_cache.retrieve(url) is None


def test_max_size_rejected(cache_dir):
    """Images exceeding max size are not stored."""
    url = "https://example.com/huge.jpg"
    data = b"x" * (image_cache._MAX_IMAGE_BYTES + 1)
    image_cache.store(url, data, "image/jpeg")
    assert image_cache.retrieve(url) is None


def test_clear(cache_dir):
    """clear() removes all entries and files."""
    image_cache.store("https://example.com/a.jpg", b"img", "image/jpeg")
    image_cache.store("https://example.com/b.jpg", b"img", "image/jpeg")
    result = image_cache.clear()
    assert result["cleared"] == 2
    assert result["freed_bytes"] > 0
    assert len(list(cache_dir.iterdir())) == 0


def test_stats(cache_dir):
    """stats() returns correct counts."""
    image_cache.store("https://example.com/a.jpg", b"imgdata", "image/jpeg")
    s = image_cache.stats()
    assert s["count"] == 1
    assert s["size_bytes"] > 0
    assert "path" in s


def test_startup_scan(cache_dir):
    """startup_scan rebuilds index from disk."""
    url = "https://example.com/persist.jpg"
    image_cache.store(url, b"imgdata", "image/jpeg")
    # Clear in-memory index
    image_cache._index.clear()
    assert image_cache.retrieve(url) is None
    # Rebuild
    image_cache.startup_scan()
    assert image_cache.retrieve(url) is not None


def test_orphaned_metadata_cleaned(cache_dir):
    """startup_scan removes metadata without matching image file."""
    filename = image_cache._url_to_filename("https://example.com/ghost.jpg")
    meta = {"url": "https://example.com/ghost.jpg", "content_type": "image/jpeg",
            "cached_at": time.time(), "accessed_at": time.time(), "size": 100}
    (cache_dir / f"{filename}.json").write_text(json.dumps(meta))
    # No .img file exists
    image_cache.startup_scan()
    assert not (cache_dir / f"{filename}.json").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/services/test_image_cache.py -v`
Expected: ImportError or AttributeError (module doesn't exist yet)

- [ ] **Step 3: Implement image_cache service**

```python
# backend/services/image_cache.py
"""Disk-backed image cache with LRU eviction and TTL expiry."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from backend.config import settings

log = logging.getLogger(__name__)

_cache_dir: str = settings.image_cache_path
_index: dict[str, dict[str, Any]] = {}

_MAX_ENTRIES = 1000
_MAX_IMAGE_BYTES = 2 * 1024 * 1024  # 2 MB
_TTL_SECONDS = 7 * 24 * 3600  # 7 days


def _url_to_filename(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def _ensure_dir() -> Path:
    p = Path(_cache_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def store(url: str, data: bytes, content_type: str) -> bool:
    """Store an image in the cache. Returns False if too large."""
    if len(data) > _MAX_IMAGE_BYTES:
        return False

    # Evict LRU if full
    while len(_index) >= _MAX_ENTRIES:
        oldest_url = min(_index, key=lambda u: _index[u]["accessed_at"])
        _remove(oldest_url)

    d = _ensure_dir()
    filename = _url_to_filename(url)
    now = time.time()

    (d / f"{filename}.img").write_bytes(data)
    meta = {
        "url": url,
        "content_type": content_type,
        "cached_at": now,
        "accessed_at": now,
        "size": len(data),
    }
    (d / f"{filename}.json").write_text(json.dumps(meta))

    _index[url] = {"filename": filename, "content_type": content_type,
                    "cached_at": now, "accessed_at": now, "size": len(data)}
    return True


def retrieve(url: str) -> tuple[bytes, str] | None:
    """Retrieve a cached image. Returns (bytes, content_type) or None."""
    entry = _index.get(url)
    if entry is None:
        return None

    # Check TTL
    if time.time() - entry["cached_at"] > _TTL_SECONDS:
        _remove(url)
        return None

    d = Path(_cache_dir)
    img_path = d / f"{entry['filename']}.img"
    if not img_path.exists():
        _remove(url)
        return None

    # Update access time
    entry["accessed_at"] = time.time()
    return img_path.read_bytes(), entry["content_type"]


def _remove(url: str) -> int:
    """Remove an entry from cache. Returns freed bytes."""
    entry = _index.pop(url, None)
    if entry is None:
        return 0
    d = Path(_cache_dir)
    freed = 0
    for ext in (".img", ".json"):
        p = d / f"{entry['filename']}{ext}"
        if p.exists():
            freed += p.stat().st_size
            p.unlink()
    return freed


def clear() -> dict[str, Any]:
    """Remove all cached images. Returns stats about what was cleared."""
    count = len(_index)
    freed = 0
    for url in list(_index):
        freed += _remove(url)
    return {"success": True, "cleared": count, "freed_bytes": freed}


def stats() -> dict[str, Any]:
    """Return cache statistics."""
    total_bytes = sum(e["size"] for e in _index.values())
    oldest = min((e["cached_at"] for e in _index.values()), default=None)
    return {
        "count": len(_index),
        "size_bytes": total_bytes,
        "size_mb": round(total_bytes / 1048576, 1),
        "oldest": oldest,
        "path": _cache_dir,
    }


def startup_scan() -> None:
    """Rebuild in-memory index from disk on startup."""
    _index.clear()
    d = Path(_cache_dir)
    if not d.exists():
        return
    now = time.time()
    for meta_path in d.glob("*.json"):
        try:
            meta = json.loads(meta_path.read_text())
            img_path = meta_path.with_suffix(".img")
            if not img_path.exists():
                meta_path.unlink()
                log.debug("Removed orphaned metadata: %s", meta_path.name)
                continue
            if now - meta["cached_at"] > _TTL_SECONDS:
                meta_path.unlink()
                img_path.unlink()
                log.debug("Removed expired cache entry: %s", meta_path.name)
                continue
            _index[meta["url"]] = {
                "filename": meta_path.stem,
                "content_type": meta["content_type"],
                "cached_at": meta["cached_at"],
                "accessed_at": meta.get("accessed_at", meta["cached_at"]),
                "size": meta["size"],
            }
        except (json.JSONDecodeError, KeyError, OSError) as exc:
            log.warning("Skipping corrupt cache entry %s: %s", meta_path.name, exc)
    log.info("Image cache loaded: %d entries from %s", len(_index), _cache_dir)
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/services/test_image_cache.py -v`
Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/image_cache.py tests/services/test_image_cache.py
git commit -m "feat: add disk-backed image cache service with LRU eviction"
```

---

## Chunk 2: Images Router + Migration

### Task 3: Images Router

**Files:**
- Create: `backend/routers/images.py`
- Create: `tests/routers/test_images.py`

- [ ] **Step 1: Write router tests**

```python
# tests/routers/test_images.py
"""Tests for backend.routers.images — image proxy endpoint."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import httpx


async def test_proxy_cache_hit(app_client):
    """Cached image is served without fetching."""
    with patch("backend.routers.images.image_cache.retrieve", return_value=(b"imgdata", "image/jpeg")):
        resp = await app_client.get("/api/images/proxy?url=https://m.media-amazon.com/img.jpg")
    assert resp.status_code == 200
    assert resp.content == b"imgdata"
    assert "max-age=604800" in resp.headers["cache-control"]


async def test_proxy_cache_miss_fetches(app_client):
    """Cache miss fetches from origin and stores."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.content = b"fetched-img"
    mock_resp.headers = {"content-type": "image/png"}
    mock_resp.raise_for_status = MagicMock()

    with (
        patch("backend.routers.images.image_cache.retrieve", return_value=None),
        patch("backend.routers.images.image_cache.store"),
        patch("backend.routers.images.httpx.AsyncClient") as MockClient,
    ):
        ctx = MagicMock()
        ctx.get = MagicMock(return_value=mock_resp)
        MockClient.return_value.__aenter__ = MagicMock(return_value=ctx)
        MockClient.return_value.__aexit__ = MagicMock(return_value=False)
        resp = await app_client.get("/api/images/proxy?url=https://image.tmdb.org/poster.jpg")
    assert resp.status_code == 200


async def test_proxy_rejects_bad_host(app_client):
    """Non-allowlisted host returns 400."""
    resp = await app_client.get("/api/images/proxy?url=https://evil.com/img.jpg")
    assert resp.status_code == 400


async def test_proxy_rejects_non_http(app_client):
    """Non-HTTP scheme returns 400."""
    resp = await app_client.get("/api/images/proxy?url=ftp://example.com/img.jpg")
    assert resp.status_code == 400
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/routers/test_images.py -v`
Expected: ImportError (router doesn't exist)

- [ ] **Step 3: Implement images router**

```python
# backend/routers/images.py
"""Image proxy with disk-backed caching."""

from __future__ import annotations

from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from backend.services import image_cache

router = APIRouter(prefix="/api", tags=["images"])

_ALLOWED_IMAGE_HOSTS = {
    "m.media-amazon.com",
    "image.tmdb.org",
    "images-na.ssl-images-amazon.com",
    "coverartarchive.org",
    "ia.media-imdb.com",
}


@router.get("/images/proxy")
async def proxy_image(url: str = Query(..., description="Image URL to proxy")) -> Response:
    """Proxy and cache external images to avoid browser ORB/CORS issues."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(400, "Only HTTP(S) URLs are allowed")
    if parsed.hostname not in _ALLOWED_IMAGE_HOSTS:
        raise HTTPException(400, "Image host not allowed")

    # Cache hit
    cached = image_cache.retrieve(url)
    if cached is not None:
        content, content_type = cached
        return Response(content=content, media_type=content_type,
                        headers={"Cache-Control": "public, max-age=604800"})

    # Fetch from origin
    validated_url = parsed.geturl()
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(validated_url)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "image/jpeg")
            image_cache.store(url, resp.content, content_type)
            return Response(content=resp.content, media_type=content_type,
                            headers={"Cache-Control": "public, max-age=604800"})
    except httpx.HTTPError:
        raise HTTPException(502, "Failed to fetch image")
```

- [ ] **Step 4: Register router in main.py**

Add `images` to the imports and `app.include_router(images.router)`.

- [ ] **Step 5: Add startup_scan to lifespan**

In `backend/main.py` lifespan, add after `system_cache.refresh()`:

```python
from backend.services import image_cache
image_cache.startup_scan()
```

- [ ] **Step 6: Run tests**

Run: `.venv/bin/python -m pytest tests/routers/test_images.py -v`
Expected: All 4 tests PASS

- [ ] **Step 7: Commit**

```bash
git add backend/routers/images.py backend/main.py tests/routers/test_images.py
git commit -m "feat: add /api/images/proxy route with disk-backed cache"
```

### Task 4: Migrate from folder.py + Update Frontend

**Files:**
- Modify: `backend/routers/folder.py:53-109`
- Modify: `frontend/src/lib/utils/poster.ts`
- Modify: `frontend/src/lib/__tests__/poster.test.ts`

- [ ] **Step 1: Replace old proxy in folder.py with 301 redirect**

Remove the cache dict, allowlist, and proxy function. Replace with:

```python
from fastapi.responses import RedirectResponse

@router.get("/poster-proxy")
async def poster_proxy_redirect(url: str = Query(...)):
    """Redirect to new image proxy endpoint."""
    return RedirectResponse(f"/api/images/proxy?url={url}", status_code=301)
```

- [ ] **Step 2: Update posterSrc() URL**

```typescript
// frontend/src/lib/utils/poster.ts
return `/api/images/proxy?url=${encodeURIComponent(url)}`;
```

- [ ] **Step 3: Update poster tests**

Replace `/api/jobs/folder/poster-proxy` with `/api/images/proxy` in both test expectations.

- [ ] **Step 4: Run frontend build + tests**

Run: `cd frontend && npm run build && npx vitest run src/lib/__tests__/poster.test.ts`
Expected: Build succeeds, tests pass

- [ ] **Step 5: Run full backend tests**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add backend/routers/folder.py frontend/src/lib/utils/poster.ts frontend/src/lib/__tests__/poster.test.ts
git commit -m "feat: migrate poster proxy to /api/images/proxy with 301 redirect"
```

---

## Chunk 3: Maintenance Endpoints + Frontend + Docker

### Task 5: Maintenance Cache Endpoints

**Files:**
- Modify: `backend/routers/maintenance.py`
- Modify: `tests/routers/test_maintenance.py`

- [ ] **Step 1: Write tests**

```python
# Add to tests/routers/test_maintenance.py

async def test_image_cache_stats(app_client):
    with patch("backend.routers.maintenance.image_cache.stats", return_value={
        "count": 5, "size_bytes": 250000, "size_mb": 0.2, "oldest": 1711234567.0, "path": "/data/cache/images"
    }):
        resp = await app_client.get("/api/maintenance/image-cache-stats")
    assert resp.status_code == 200
    assert resp.json()["count"] == 5


async def test_clear_image_cache(app_client):
    with patch("backend.routers.maintenance.image_cache.clear", return_value={
        "success": True, "cleared": 5, "freed_bytes": 250000
    }):
        resp = await app_client.post("/api/maintenance/clear-image-cache")
    assert resp.status_code == 200
    assert resp.json()["cleared"] == 5
```

- [ ] **Step 2: Add endpoints to maintenance.py**

```python
# Add import at top
from backend.services import image_cache

# Add after cleanup_transcoder endpoint

@router.get("/maintenance/image-cache-stats")
def get_image_cache_stats():
    """Return image cache statistics."""
    return image_cache.stats()


@router.post("/maintenance/clear-image-cache")
def clear_image_cache():
    """Clear all cached images."""
    return image_cache.clear()
```

- [ ] **Step 3: Run tests**

Run: `.venv/bin/python -m pytest tests/routers/test_maintenance.py -v`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add backend/routers/maintenance.py tests/routers/test_maintenance.py
git commit -m "feat: add image cache stats and clear endpoints to maintenance"
```

### Task 6: Frontend Maintenance UI

**Files:**
- Modify: `frontend/src/lib/api/maintenance.ts`
- Modify: `frontend/src/routes/maintenance/+page.svelte`

- [ ] **Step 1: Add API functions**

```typescript
// Add to frontend/src/lib/api/maintenance.ts

export interface ImageCacheStats {
	count: number;
	size_bytes: number;
	size_mb: number;
	oldest: number | null;
	path: string;
}

export function fetchImageCacheStats(): Promise<ImageCacheStats> {
	return apiFetch('/api/maintenance/image-cache-stats');
}

export function clearImageCache(): Promise<{ success: boolean; cleared: number; freed_bytes: number }> {
	return apiFetch('/api/maintenance/clear-image-cache', { method: 'POST' });
}
```

- [ ] **Step 2: Add cache section to maintenance page**

Add an "Image Cache" card to the maintenance page showing:
- Count and size from stats
- "Clear Cache" button with confirmation
- Success feedback after clearing

Follow the existing card pattern used for notifications and transcoder cleanup.

- [ ] **Step 3: Build and verify**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/api/maintenance.ts frontend/src/routes/maintenance/+page.svelte
git commit -m "feat: add image cache section to maintenance page"
```

### Task 7: Docker Compose Updates

**Files:**
- Modify: `docker-compose.yml` (UI repo)
- Modify: `docker-compose.yml` (ARM-neu — separate PR)
- Modify: `docker-compose.remote-transcoder.yml` (ARM-neu)
- Modify: `docker-compose.dev.yml` (ARM-neu)

- [ ] **Step 1: Update UI docker-compose.yml**

Add to arm-ui service environment:
```yaml
      - ARM_UI_IMAGE_CACHE_PATH=/data/cache/images
```

Add to arm-ui service volumes:
```yaml
      - image-cache:/data/cache/images:rw
```

Add to top-level volumes:
```yaml
  image-cache:
```

- [ ] **Step 2: Commit UI compose change**

```bash
git add docker-compose.yml
git commit -m "feat: add image cache volume to docker-compose"
```

- [ ] **Step 3: Update ARM-neu compose files (separate branch/PR)**

For `docker-compose.yml` and `docker-compose.remote-transcoder.yml`, add to arm-ui service:
```yaml
      - ARM_UI_IMAGE_CACHE_PATH=/data/cache/images
```
```yaml
      - image-cache:/data/cache/images:rw
```

Add `image-cache:` to top-level volumes.

For `docker-compose.dev.yml`, add to arm-ui:
```yaml
      - ./dev-data/cache/images:/data/cache/images:rw
```

- [ ] **Step 4: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: All pass

- [ ] **Step 5: Run frontend build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 6: Final commit and push**

```bash
git push -u origin feat/image-proxy-cache
```

Create PR. Verify all CI passes.

---

## Post-Implementation

- Create separate PR in ARM-neu for compose file updates
- Close issue #38
- Deploy to hifi-server
