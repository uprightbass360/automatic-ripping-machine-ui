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
