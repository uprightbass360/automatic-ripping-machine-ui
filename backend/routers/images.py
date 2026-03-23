"""Image proxy with disk-backed caching."""

from __future__ import annotations

from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from backend.services import image_cache

router = APIRouter(prefix="/api", tags=["images"])

_SAFE_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml",
}

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

    # Use the validated/reconstructed URL to break taint chain
    safe_url = parsed.geturl()

    # Cache hit
    cached = image_cache.retrieve(safe_url)
    if cached is not None:
        content, content_type = cached
        # Sanitize content_type to known image types
        safe_type = content_type if content_type in _SAFE_CONTENT_TYPES else "application/octet-stream"
        return Response(content=content, media_type=safe_type,
                        headers={"Cache-Control": "public, max-age=604800"})

    # Fetch from origin
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(safe_url)  # NOSONAR — host validated above
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "image/jpeg")
            safe_type = content_type if content_type in _SAFE_CONTENT_TYPES else "image/jpeg"
            image_cache.store(safe_url, resp.content, safe_type)
            return Response(content=resp.content, media_type=safe_type,
                            headers={"Cache-Control": "public, max-age=604800"})
    except httpx.HTTPError:
        raise HTTPException(502, "Failed to fetch image")
