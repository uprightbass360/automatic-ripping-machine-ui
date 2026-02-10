"""ARM log file reader service."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from backend.config import settings


def _log_dir() -> Path:
    return Path(settings.arm_log_path)


def list_logs() -> list[dict]:
    """List all log files in the ARM log directory."""
    log_dir = _log_dir()
    if not log_dir.is_dir():
        return []

    logs = []
    for entry in sorted(log_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if entry.is_file() and entry.suffix == ".log":
            stat = entry.stat()
            logs.append({
                "filename": entry.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            })
    return logs


def read_log(
    filename: str,
    mode: str = "tail",
    lines: int = 100,
) -> dict | None:
    """Read a log file. Mode is 'tail' (last N lines) or 'full'."""
    log_path = _log_dir() / filename

    # Prevent path traversal
    try:
        log_path = log_path.resolve()
        if not str(log_path).startswith(str(_log_dir().resolve())):
            return None
    except (OSError, ValueError):
        return None

    if not log_path.is_file():
        return None

    try:
        with open(log_path, "r", errors="replace") as f:
            if mode == "full":
                content = f.read()
                line_count = content.count("\n")
            else:
                all_lines = f.readlines()
                tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
                content = "".join(tail)
                line_count = len(tail)
    except OSError:
        return None

    return {
        "filename": filename,
        "content": content,
        "lines": line_count,
    }
