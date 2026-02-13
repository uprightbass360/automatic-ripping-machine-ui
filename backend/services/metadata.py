"""Metadata search service — queries OMDb or TMDb for title information."""

from __future__ import annotations

import logging
import os
import re
from functools import lru_cache
from typing import Any

import httpx
import yaml

from backend.config import settings

log = logging.getLogger(__name__)

TMDB_YEAR_REGEX = r"-\d{0,2}-\d{0,2}"
TMDB_POSTER_BASE = "https://image.tmdb.org/t/p/original"


@lru_cache(maxsize=1)
def _get_api_keys() -> dict[str, str | None]:
    """Read METADATA_PROVIDER and API keys from arm.yaml. Cached at process level."""
    yaml_path = settings.arm_config_path
    if not yaml_path or not os.path.isfile(yaml_path):
        log.warning("arm.yaml not found at %s", yaml_path)
        return {"provider": "omdb", "omdb_key": None, "tmdb_key": None}
    try:
        with open(yaml_path, "r") as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        log.warning("Failed to read arm.yaml: %s", e)
        return {"provider": "omdb", "omdb_key": None, "tmdb_key": None}
    provider = str(config.get("METADATA_PROVIDER", "omdb")).lower()
    return {
        "provider": provider,
        "omdb_key": config.get("OMDB_API_KEY"),
        "tmdb_key": config.get("TMDB_API_KEY"),
    }


def _http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=15.0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def search(query: str, year: str | None = None) -> list[dict[str, Any]]:
    """Search for titles. Returns normalized list of SearchResult dicts."""
    keys = _get_api_keys()
    if keys["provider"] == "tmdb" and keys["tmdb_key"]:
        return await _tmdb_search(query, year, keys["tmdb_key"])
    if keys["omdb_key"]:
        return await _omdb_search(query, year, keys["omdb_key"])
    log.warning("No API key configured for provider=%s", keys["provider"])
    return []


async def get_details(imdb_id: str) -> dict[str, Any] | None:
    """Fetch full details for a single title by IMDb ID."""
    keys = _get_api_keys()
    if keys["provider"] == "tmdb" and keys["tmdb_key"]:
        return await _tmdb_find(imdb_id, keys["tmdb_key"])
    if keys["omdb_key"]:
        return await _omdb_details(imdb_id, keys["omdb_key"])
    return None


# ---------------------------------------------------------------------------
# OMDb helpers
# ---------------------------------------------------------------------------


async def _omdb_search(query: str, year: str | None, api_key: str) -> list[dict[str, Any]]:
    params: dict[str, str] = {"s": query, "r": "json", "apikey": api_key}
    if year:
        params["y"] = year
    async with _http_client() as client:
        resp = await client.get("https://www.omdbapi.com/", params=params)
        data = resp.json()

    results = []
    if data.get("Response") == "True" and "Search" in data:
        for item in data["Search"]:
            results.append(_normalize_omdb(item))
        return results

    # Fallback: ?t= exact match for short/numeric titles
    params_t: dict[str, str] = {"t": query, "r": "json", "apikey": api_key}
    if year:
        params_t["y"] = year
    async with _http_client() as client:
        resp = await client.get("https://www.omdbapi.com/", params=params_t)
        data = resp.json()
    if data.get("Response") == "True":
        results.append(_normalize_omdb(data))
    return results


def _normalize_omdb(item: dict) -> dict[str, Any]:
    media_type = (item.get("Type") or "movie").lower()
    if media_type == "series":
        pass  # keep as series
    else:
        media_type = "movie"
    poster = item.get("Poster")
    if poster == "N/A":
        poster = None
    return {
        "title": item.get("Title", ""),
        "year": item.get("Year", ""),
        "imdb_id": item.get("imdbID"),
        "media_type": media_type,
        "poster_url": poster,
    }


async def _omdb_details(imdb_id: str, api_key: str) -> dict[str, Any] | None:
    params = {"i": imdb_id, "plot": "short", "r": "json", "apikey": api_key}
    async with _http_client() as client:
        resp = await client.get("https://www.omdbapi.com/", params=params)
        data = resp.json()
    if data.get("Response") != "True":
        return None
    result = _normalize_omdb(data)
    plot = data.get("Plot")
    result["plot"] = plot if plot != "N/A" else None
    result["background_url"] = None  # OMDb has no background images
    return result


# ---------------------------------------------------------------------------
# TMDb helpers
# ---------------------------------------------------------------------------


async def _tmdb_search(query: str, year: str | None, api_key: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    # Try movies first
    params: dict[str, str] = {"api_key": api_key, "query": query}
    if year:
        params["year"] = year
    async with _http_client() as client:
        resp = await client.get(
            "https://api.themoviedb.org/3/search/movie", params=params
        )
        data = resp.json()

    if data.get("total_results", 0) > 0:
        for item in data["results"]:
            results.append(await _normalize_tmdb(item, "movie", api_key))
        return results

    # Fallback to TV
    params_tv: dict[str, str] = {"api_key": api_key, "query": query}
    if year:
        params_tv["first_air_date_year"] = year
    async with _http_client() as client:
        resp = await client.get(
            "https://api.themoviedb.org/3/search/tv", params=params_tv
        )
        data = resp.json()

    if data.get("total_results", 0) > 0:
        for item in data["results"]:
            results.append(await _normalize_tmdb(item, "series", api_key))
    return results


async def _normalize_tmdb(
    item: dict, media_type: str, api_key: str
) -> dict[str, Any]:
    title = item.get("title") or item.get("name", "")
    release = item.get("release_date") or item.get("first_air_date") or ""
    year = re.sub(TMDB_YEAR_REGEX, "", release) if release else ""
    poster_path = item.get("poster_path")
    poster_url = f"{TMDB_POSTER_BASE}{poster_path}" if poster_path else None
    imdb_id = await _tmdb_get_imdb(item["id"], media_type, api_key)
    return {
        "title": title,
        "year": year,
        "imdb_id": imdb_id,
        "media_type": media_type,
        "poster_url": poster_url,
    }


async def _tmdb_get_imdb(
    tmdb_id: int, media_type: str, api_key: str
) -> str | None:
    """Get the IMDb ID for a TMDb entry."""
    async with _http_client() as client:
        # Try movie endpoint first
        resp = await client.get(
            f"https://api.themoviedb.org/3/movie/{tmdb_id}",
            params={"api_key": api_key, "append_to_response": "external_ids"},
        )
        data = resp.json()
        if "status_code" not in data:
            return data.get("external_ids", {}).get("imdb_id")

        # Fallback to TV external IDs
        resp = await client.get(
            f"https://api.themoviedb.org/3/tv/{tmdb_id}/external_ids",
            params={"api_key": api_key},
        )
        data = resp.json()
        if "status_code" not in data:
            return data.get("imdb_id")
    return None


async def _tmdb_find(imdb_id: str, api_key: str) -> dict[str, Any] | None:
    """Lookup full details by IMDb ID via TMDb /find endpoint."""
    async with _http_client() as client:
        resp = await client.get(
            f"https://api.themoviedb.org/3/find/{imdb_id}",
            params={"api_key": api_key, "external_source": "imdb_id"},
        )
        data = resp.json()

    # Check movie results first, then TV
    item = None
    media_type = "movie"
    if data.get("movie_results"):
        item = data["movie_results"][0]
    elif data.get("tv_results"):
        item = data["tv_results"][0]
        media_type = "series"

    if not item:
        return None

    title = item.get("title") or item.get("name", "")
    release = item.get("release_date") or item.get("first_air_date") or ""
    year = re.sub(TMDB_YEAR_REGEX, "", release) if release else ""
    poster_path = item.get("poster_path")
    backdrop_path = item.get("backdrop_path")

    return {
        "title": title,
        "year": year,
        "imdb_id": imdb_id,
        "media_type": media_type,
        "poster_url": f"{TMDB_POSTER_BASE}{poster_path}" if poster_path else None,
        "plot": item.get("overview") or None,
        "background_url": f"{TMDB_POSTER_BASE}{backdrop_path}" if backdrop_path else None,
    }
