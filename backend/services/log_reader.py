"""ARM log file reader service."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from backend.config import settings

# ARM plain text log format: "{timestamp} {logger}: {LEVEL}: {message}"
# e.g. "02-28-2026 04:59:16 ARM: INFO: Ripping complete"
_ARM_PLAIN_RE = re.compile(
    r'^(.+?)\s+(\w+):\s+(DEBUG|INFO|WARNING|ERROR|CRITICAL):\s*(.*)',
    re.IGNORECASE,
)

# Wrapper script format: "{weekday} {month} {day} {time} [{AM/PM}] {TZ} {year} [{logger}] {message}"
# e.g. "Sun Mar  1 04:34:15 EST 2026 [ARM] Starting ARM for DVD on sr0"
# e.g. "Fri Apr  3 12:14:15 PM EDT 2026 [ARM] Entering docker wrapper for sr0"
_WRAPPER_BRACKET_RE = re.compile(
    r'^(\w{3}\s+\w{3}\s+\d+\s+[\d:]+(?:\s+[AP]M)?\s+\w+\s+\d{4})\s+\[(\w+)\]\s*(.*)',
)

# ISO timestamp with bracket logger: "{YYYY-MM-DD HH:MM:SS} [{logger}] {message}"
# e.g. "2026-03-20 14:24:48 [rescan_drive] No disc in /dev/sr0"
_ISO_BRACKET_RE = re.compile(
    r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[(\w+)\]\s*(.*)',
)

# Wrapper script format without logger: "{timestamp} {message}"
# e.g. "Sun Mar  1 04:34:15 EST 2026 Entering docker wrapper"
_WRAPPER_PLAIN_RE = re.compile(
    r'^(\w{3}\s+\w{3}\s+\d+\s+[\d:]+(?:\s+[AP]M)?\s+\w+\s+\d{4})\s+(.*)',
)


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


def resolve_log_path(filename: str) -> Path | None:
    """Resolve a log filename to an absolute path, with traversal protection."""
    log_path = _log_dir() / filename
    try:
        log_path = log_path.resolve()
        if not str(log_path).startswith(str(_log_dir().resolve())):
            return None
    except (OSError, ValueError):
        return None
    if not log_path.is_file():
        return None
    return log_path


def delete_log(filename: str) -> bool:
    """Delete a log file. Returns True on success, False if not found."""
    log_path = resolve_log_path(filename)
    if log_path is None:
        return False
    try:
        log_path.unlink()
        return True
    except OSError:
        return False


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


def _parse_log_line(line: str) -> dict:
    """Parse a single log line. Tries JSON first, then ARM plain text, then raw fallback."""
    line = line.rstrip("\n")
    # JSON lines (structlog format)
    try:
        parsed = json.loads(line)
        return {
            "timestamp": parsed.get("timestamp", ""),
            "level": parsed.get("level", "info"),
            "logger": parsed.get("logger", ""),
            "event": parsed.get("event", ""),
            "job_id": parsed.get("job_id"),
            "label": parsed.get("label"),
            "raw": line,
        }
    except (json.JSONDecodeError, TypeError):
        pass

    # ARM plain text format: "{timestamp} {logger}: {LEVEL}: {message}"
    m = _ARM_PLAIN_RE.match(line)
    if m:
        return {
            "timestamp": m.group(1).strip(),
            "level": m.group(3).lower(),
            "logger": m.group(2),
            "event": m.group(4),
            "job_id": None,
            "label": None,
            "raw": line,
        }

    # Wrapper script format with [LOGGER]: "Sat Apr 4 02:33:31 EDT 2026 [ARM] message"
    m = _WRAPPER_BRACKET_RE.match(line)
    if m:
        return {
            "timestamp": m.group(1).strip(),
            "level": "info",
            "logger": m.group(2),
            "event": m.group(3),
            "job_id": None,
            "label": None,
            "raw": line,
        }

    # ISO timestamp with bracket logger: "2026-03-20 14:24:48 [rescan_drive] message"
    m = _ISO_BRACKET_RE.match(line)
    if m:
        return {
            "timestamp": m.group(1).strip(),
            "level": "info",
            "logger": m.group(2),
            "event": m.group(3),
            "job_id": None,
            "label": None,
            "raw": line,
        }

    # Wrapper script format without logger: "Sat Apr 4 02:33:31 EDT 2026 message"
    m = _WRAPPER_PLAIN_RE.match(line)
    if m:
        return {
            "timestamp": m.group(1).strip(),
            "level": "info",
            "logger": "wrapper",
            "event": m.group(2),
            "job_id": None,
            "label": None,
            "raw": line,
        }

    # Fallback: entire line as event
    return {
        "timestamp": "",
        "level": "info",
        "logger": "",
        "event": line,
        "job_id": None,
        "label": None,
        "raw": line,
    }


def read_structured_log(
    filename: str,
    mode: str = "tail",
    lines: int = 100,
    level: str | None = None,
    search: str | None = None,
) -> dict | None:
    """Read and parse a structured log file with optional filtering."""
    raw = read_log(filename, mode=mode, lines=lines)
    if raw is None:
        return None

    entries = [_parse_log_line(l) for l in raw["content"].splitlines() if l.strip()]

    if level:
        entries = [e for e in entries if e["level"] == level.lower()]
    if search:
        search_lower = search.lower()
        entries = [e for e in entries if search_lower in e["event"].lower()]

    return {"filename": filename, "entries": entries, "lines": len(entries)}
