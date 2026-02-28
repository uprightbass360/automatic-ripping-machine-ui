"""Tests for backend.services.log_reader — pure FS logic + path traversal."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from backend.services import log_reader


def test_list_logs_empty_dir(tmp_path: Path):
    """list_logs() returns [] for an empty directory."""
    with patch.object(log_reader, "_log_dir", return_value=tmp_path):
        assert log_reader.list_logs() == []


def test_list_logs_nonexistent_dir(tmp_path: Path):
    """list_logs() returns [] when the log directory does not exist."""
    missing = tmp_path / "no_such_dir"
    with patch.object(log_reader, "_log_dir", return_value=missing):
        assert log_reader.list_logs() == []


def test_list_logs_filters_non_log_files(tmp_path: Path):
    """Only .log files are returned; .txt, .bak, etc. are excluded."""
    (tmp_path / "arm.log").write_text("log content")
    (tmp_path / "notes.txt").write_text("not a log")
    (tmp_path / "backup.bak").write_text("not a log")
    with patch.object(log_reader, "_log_dir", return_value=tmp_path):
        logs = log_reader.list_logs()
    assert len(logs) == 1
    assert logs[0]["filename"] == "arm.log"


def test_list_logs_sort_order(tmp_path: Path):
    """Logs are sorted newest-first by mtime."""
    f1 = tmp_path / "old.log"
    f2 = tmp_path / "new.log"
    f1.write_text("old")
    f2.write_text("new")
    # Force mtime: old=1000, new=2000
    os.utime(f1, (1000, 1000))
    os.utime(f2, (2000, 2000))
    with patch.object(log_reader, "_log_dir", return_value=tmp_path):
        logs = log_reader.list_logs()
    assert logs[0]["filename"] == "new.log"
    assert logs[1]["filename"] == "old.log"


def test_list_logs_returns_size_and_modified(tmp_path: Path):
    """Each entry has filename, size, and modified (UTC datetime)."""
    (tmp_path / "test.log").write_text("hello")
    with patch.object(log_reader, "_log_dir", return_value=tmp_path):
        logs = log_reader.list_logs()
    entry = logs[0]
    assert entry["filename"] == "test.log"
    assert entry["size"] == 5
    assert isinstance(entry["modified"], datetime)
    assert entry["modified"].tzinfo == timezone.utc


def test_read_log_path_traversal_blocked(tmp_path: Path):
    """Attempting path traversal (../) returns None."""
    secret = tmp_path / "secret.txt"
    secret.write_text("top secret")
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    with patch.object(log_reader, "_log_dir", return_value=log_dir):
        result = log_reader.read_log("../secret.txt")
    assert result is None


def test_read_log_tail_mode(tmp_path: Path):
    """Tail mode returns the last N lines."""
    log_file = tmp_path / "job.log"
    lines = [f"line {i}\n" for i in range(20)]
    log_file.write_text("".join(lines))
    with patch.object(log_reader, "_log_dir", return_value=tmp_path):
        result = log_reader.read_log("job.log", mode="tail", lines=5)
    assert result is not None
    assert result["lines"] == 5
    assert "line 15" in result["content"]
    assert "line 19" in result["content"]


def test_read_log_full_mode(tmp_path: Path):
    """Full mode reads the entire file."""
    log_file = tmp_path / "full.log"
    log_file.write_text("line1\nline2\nline3\n")
    with patch.object(log_reader, "_log_dir", return_value=tmp_path):
        result = log_reader.read_log("full.log", mode="full")
    assert result is not None
    assert result["filename"] == "full.log"
    assert "line1" in result["content"]
    assert "line3" in result["content"]
    assert result["lines"] == 3


def test_read_log_missing_file(tmp_path: Path):
    """Reading a nonexistent log file returns None."""
    with patch.object(log_reader, "_log_dir", return_value=tmp_path):
        result = log_reader.read_log("no_such.log")
    assert result is None


# --- Structured log parsing tests ---


def test_parse_json_line():
    """Valid JSON line is parsed into structured fields."""
    line = json.dumps({
        "timestamp": "2026-02-28T10:15:30Z",
        "level": "info",
        "logger": "arm.ripper.makemkv",
        "event": "Ripping title 1",
        "job_id": 5,
        "label": "LOTR",
    })
    entry = log_reader._parse_log_line(line)
    assert entry["timestamp"] == "2026-02-28T10:15:30Z"
    assert entry["level"] == "info"
    assert entry["logger"] == "arm.ripper.makemkv"
    assert entry["event"] == "Ripping title 1"
    assert entry["job_id"] == 5
    assert entry["label"] == "LOTR"
    assert entry["raw"] == line


def test_parse_plain_text_line():
    """ARM plain text line is parsed via regex into structured fields."""
    line = "2024-01-01 10:00:00 ARM: INFO: Ripping started"
    entry = log_reader._parse_log_line(line)
    assert entry["timestamp"] == "2024-01-01 10:00:00"
    assert entry["level"] == "info"
    assert entry["logger"] == "ARM"
    assert entry["event"] == "Ripping started"
    assert entry["job_id"] is None
    assert entry["label"] is None
    assert entry["raw"] == line


def test_parse_unstructured_line():
    """Non-JSON, non-ARM line falls back to raw wrapper."""
    line = "Some random unstructured text"
    entry = log_reader._parse_log_line(line)
    assert entry["timestamp"] == ""
    assert entry["level"] == "info"
    assert entry["event"] == line
    assert entry["job_id"] is None
    assert entry["raw"] == line


def test_read_structured_log_filters_by_level(tmp_path: Path):
    """Level filter returns only matching entries."""
    log_file = tmp_path / "job.log"
    lines = [
        json.dumps({"level": "info", "event": "Starting rip"}),
        json.dumps({"level": "error", "event": "Disc read failed"}),
        json.dumps({"level": "info", "event": "Retrying"}),
        json.dumps({"level": "warning", "event": "Slow read"}),
    ]
    log_file.write_text("\n".join(lines) + "\n")
    with patch.object(log_reader, "_log_dir", return_value=tmp_path):
        result = log_reader.read_structured_log("job.log", mode="full", level="error")
    assert result is not None
    assert result["lines"] == 1
    assert result["entries"][0]["event"] == "Disc read failed"


def test_read_structured_log_filters_by_search(tmp_path: Path):
    """Search filter matches event text case-insensitively."""
    log_file = tmp_path / "job.log"
    lines = [
        json.dumps({"level": "info", "event": "Ripping title 1"}),
        json.dumps({"level": "info", "event": "Ripping title 2"}),
        json.dumps({"level": "info", "event": "Transcoding complete"}),
    ]
    log_file.write_text("\n".join(lines) + "\n")
    with patch.object(log_reader, "_log_dir", return_value=tmp_path):
        result = log_reader.read_structured_log("job.log", mode="full", search="ripping")
    assert result is not None
    assert result["lines"] == 2
    assert all("Ripping" in e["event"] for e in result["entries"])


def test_mixed_format_log(tmp_path: Path):
    """Handles mix of JSON and plain text lines gracefully."""
    log_file = tmp_path / "mixed.log"
    content = (
        "Plain text startup message\n"
        + json.dumps({"level": "info", "event": "Structured log", "job_id": 1}) + "\n"
        + "Another plain text line\n"
        + json.dumps({"level": "error", "event": "Something broke", "job_id": 1}) + "\n"
    )
    log_file.write_text(content)
    with patch.object(log_reader, "_log_dir", return_value=tmp_path):
        result = log_reader.read_structured_log("mixed.log", mode="full")
    assert result is not None
    assert result["lines"] == 4
    # First entry is plain text
    assert result["entries"][0]["event"] == "Plain text startup message"
    assert result["entries"][0]["job_id"] is None
    # Second entry is JSON
    assert result["entries"][1]["event"] == "Structured log"
    assert result["entries"][1]["job_id"] == 1
    # Fourth entry is error
    assert result["entries"][3]["level"] == "error"
