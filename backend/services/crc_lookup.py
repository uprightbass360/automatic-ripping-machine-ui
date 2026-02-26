"""Async lookup against the ARM CRC64 community database."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from backend.config import settings

log = logging.getLogger(__name__)

CRC_DB_URL = "https://1337server.pythonanywhere.com/api/v1/"


def has_api_key() -> bool:
    """Check whether ARM_API_KEY is configured in arm.yaml."""
    yaml_path = settings.arm_config_path
    if not yaml_path or not os.path.isfile(yaml_path):
        return False
    try:
        import yaml
        with open(yaml_path, "r") as f:
            config = yaml.safe_load(f)
        return bool(config and config.get("ARM_API_KEY"))
    except Exception:
        return False


async def lookup_crc(crc64: str) -> dict[str, Any]:
    """Search the CRC64 database for a disc hash.

    Returns {"found": bool, "results": [...]} on success,
    or {"found": false, "results": [], "error": "..."} on failure.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(CRC_DB_URL, params={"mode": "s", "crc64": crc64})
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return {"found": False, "results": [], "error": "CRC database unreachable"}

    if not data.get("success"):
        return {"found": False, "results": []}

    raw = data.get("results", {})
    results = []
    for entry in raw.values():
        results.append({
            "title": entry.get("title", ""),
            "year": entry.get("year", ""),
            "imdb_id": entry.get("imdb_id", ""),
            "tmdb_id": entry.get("tmdb_id", ""),
            "video_type": entry.get("video_type", ""),
            "disctype": entry.get("disctype", ""),
            "label": entry.get("label", ""),
            "poster_url": entry.get("poster_img", ""),
            "hasnicetitle": entry.get("hasnicetitle", ""),
            "validated": entry.get("validated", ""),
            "date_added": entry.get("date_added", ""),
        })

    return {"found": len(results) > 0, "results": results}
