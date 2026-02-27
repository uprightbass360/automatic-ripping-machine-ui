"""MusicBrainz metadata search service for audio CDs."""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

log = logging.getLogger(__name__)

MUSICBRAINZ_BASE = "https://musicbrainz.org/ws/2"
COVERART_BASE = "https://coverartarchive.org/release"
USER_AGENT = "ARM-UI/1.0 (https://github.com/uprightbass360/automatic-ripping-machine-neu)"


def _http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=15.0,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )


def _build_artist_credit(credits: list[dict]) -> str:
    """Join all artist-credit entries with their joinphrases."""
    parts: list[str] = []
    for entry in credits:
        parts.append(entry.get("name", ""))
        jp = entry.get("joinphrase", "")
        if jp:
            parts.append(jp)
    return "".join(parts)


def _extract_label(label_info: list[dict]) -> str | None:
    if label_info and label_info[0].get("label"):
        return label_info[0]["label"].get("name")
    return None


def _extract_catalog_number(label_info: list[dict]) -> str | None:
    if label_info:
        return label_info[0].get("catalog-number")
    return None


def _extract_format(media: list[dict]) -> str | None:
    if media:
        return media[0].get("format")
    return None


# Lucene special characters that must be escaped in user-provided search terms.
_LUCENE_SPECIAL = re.compile(r'([+\-&|!(){}\[\]^"~*?:\\/<>])')


def _escape_lucene(text: str) -> str:
    """Escape Lucene special characters in user input."""
    return _LUCENE_SPECIAL.sub(r"\\\1", text)


async def search(
    query: str,
    artist: str | None = None,
    release_type: str | None = None,
    format: str | None = None,
    country: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """Search MusicBrainz for releases matching query text and optional filters."""
    safe_query = _escape_lucene(query)
    parts: list[str] = []
    if artist:
        safe_artist = _escape_lucene(artist)
        parts.append(f'release:"{safe_query}" AND artist:"{safe_artist}"')
    else:
        parts.append(safe_query)
    if release_type:
        parts.append(f"AND type:{release_type}")
    if format:
        parts.append(f'AND format:"{format}"')
    if country:
        parts.append(f"AND country:{country}")
    if status:
        parts.append(f"AND status:{status}")
    lucene_query = " ".join(parts)

    params = {"query": lucene_query, "fmt": "json", "limit": "15"}

    async with _http_client() as client:
        resp = await client.get(f"{MUSICBRAINZ_BASE}/release", params=params)
        resp.raise_for_status()
        data = resp.json()

    results: list[dict[str, Any]] = []
    for release in data.get("releases", []):
        mbid = release.get("id", "")

        artist_credit = release.get("artist-credit", [])
        artist_name = _build_artist_credit(artist_credit)

        date = release.get("date", "")
        year = date[:4] if date else ""

        track_count = release.get("track-count")
        media = release.get("media", [])
        label_info = release.get("label-info", [])
        release_group = release.get("release-group", {})

        results.append({
            "title": release.get("title", ""),
            "artist": artist_name,
            "year": year,
            "release_id": mbid,
            "media_type": "music",
            "poster_url": f"{COVERART_BASE}/{mbid}/front-250" if mbid else None,
            "track_count": track_count,
            "country": release.get("country"),
            "release_type": release_group.get("primary-type"),
            "format": _extract_format(media),
            "label": _extract_label(label_info),
        })
    return results


async def get_details(release_id: str) -> dict[str, Any] | None:
    """Fetch full release details from MusicBrainz by release MBID."""
    params = {
        "inc": "artist-credits+recordings+release-groups+labels",
        "fmt": "json",
    }

    async with _http_client() as client:
        resp = await client.get(
            f"{MUSICBRAINZ_BASE}/release/{release_id}", params=params
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()

    mbid = data.get("id", release_id)

    artist_credit = data.get("artist-credit", [])
    artist_name = _build_artist_credit(artist_credit)

    date = data.get("date", "")
    year = date[:4] if date else ""

    label_info = data.get("label-info", [])
    media = data.get("media", [])
    release_group = data.get("release-group", {})

    tracks: list[dict[str, Any]] = []
    track_count = 0
    for medium in media:
        for track in medium.get("tracks", []):
            recording = track.get("recording", {})
            length_ms = track.get("length") or recording.get("length")
            tracks.append({
                "number": track.get("number", ""),
                "title": recording.get("title", track.get("title", "")),
                "length_ms": length_ms,
            })
        track_count += medium.get("track-count", 0)

    return {
        "title": data.get("title", ""),
        "artist": artist_name,
        "year": year,
        "release_id": mbid,
        "media_type": "music",
        "poster_url": f"{COVERART_BASE}/{mbid}/front-250",
        "track_count": track_count or len(tracks),
        "country": data.get("country"),
        "release_type": release_group.get("primary-type"),
        "format": _extract_format(media),
        "label": _extract_label(label_info),
        "catalog_number": _extract_catalog_number(label_info),
        "barcode": data.get("barcode") or None,
        "status": data.get("status"),
        "tracks": tracks,
    }
