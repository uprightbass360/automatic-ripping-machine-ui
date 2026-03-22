"""Tests for log_reader.resolve_log_path() and delete_log()."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from backend.services import log_reader


def test_resolve_log_path_existing_file(tmp_path: Path):
    """resolve_log_path() returns absolute path for an existing log file."""
    log_file = tmp_path / "arm.log"
    log_file.write_text("log content")
    with patch.object(log_reader, "_log_dir", return_value=tmp_path):
        result = log_reader.resolve_log_path("arm.log")
    assert result is not None
    assert result == log_file.resolve()


def test_resolve_log_path_nonexistent_file(tmp_path: Path):
    """resolve_log_path() returns None when the file does not exist."""
    with patch.object(log_reader, "_log_dir", return_value=tmp_path):
        result = log_reader.resolve_log_path("no_such_file.log")
    assert result is None


def test_resolve_log_path_traversal_blocked(tmp_path: Path):
    """resolve_log_path() returns None for path traversal attempts."""
    secret = tmp_path / "passwd"
    secret.write_text("root:x:0:0")
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    with patch.object(log_reader, "_log_dir", return_value=log_dir):
        result = log_reader.resolve_log_path("../../etc/passwd")
    assert result is None


def test_resolve_log_path_traversal_with_parent_dir(tmp_path: Path):
    """resolve_log_path() rejects ../filename even when target file exists."""
    target = tmp_path / "secret.log"
    target.write_text("sensitive")
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    with patch.object(log_reader, "_log_dir", return_value=log_dir):
        result = log_reader.resolve_log_path("../secret.log")
    assert result is None


def test_delete_log_success(tmp_path: Path):
    """delete_log() returns True and removes the file."""
    log_file = tmp_path / "job_1.log"
    log_file.write_text("some log output")
    with patch.object(log_reader, "_log_dir", return_value=tmp_path):
        result = log_reader.delete_log("job_1.log")
    assert result is True
    assert not log_file.exists()


def test_delete_log_nonexistent(tmp_path: Path):
    """delete_log() returns False when the file does not exist."""
    with patch.object(log_reader, "_log_dir", return_value=tmp_path):
        result = log_reader.delete_log("missing.log")
    assert result is False


def test_delete_log_traversal_blocked(tmp_path: Path):
    """delete_log() returns False for path traversal attempts."""
    secret = tmp_path / "important.log"
    secret.write_text("do not delete")
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    with patch.object(log_reader, "_log_dir", return_value=log_dir):
        result = log_reader.delete_log("../important.log")
    assert result is False
    assert secret.exists()
