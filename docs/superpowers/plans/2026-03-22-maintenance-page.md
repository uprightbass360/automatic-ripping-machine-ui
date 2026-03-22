# Maintenance Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a standalone `/maintenance` page for system housekeeping — orphan file cleanup, notification management, transcoder job cleanup — plus fix architecture debt where the UI bypasses ARM for DB writes.

**Architecture:** ARM backend gets new maintenance endpoints for orphan detection and file deletion. UI backend proxies ARM + handles notifications and transcoder cleanup + aggregates summary counts. Frontend gets a new `/maintenance` route with four collapsible sections. Two existing UI backend endpoints are refactored to proxy through ARM instead of writing to the DB directly.

**Tech Stack:** Python/FastAPI (ARM + UI backends), SvelteKit/Svelte 5 (frontend), SQLAlchemy, httpx, Vitest + Testing Library

**Spec:** `docs/superpowers/specs/2026-03-22-maintenance-page-design.md`

**Repos:**
- ARM backend: `~/src/automatic-ripping-machine-neu` (branch `feat/maintenance`)
- UI: `~/src/automatic-ripping-machine-ui` (branch `feat/jake-maintenance`)

---

## Phase 1: ARM Backend — Maintenance Endpoints

All tasks in this phase are in `~/src/automatic-ripping-machine-neu`.

### Task 1: Maintenance Service — Orphan Detection

**Files:**
- Create: `arm/services/maintenance.py`
- Test: `test/test_maintenance_service.py`

This task builds the core orphan detection logic as a service module. No router yet — just testable functions.

- [ ] **Step 1: Write tests for orphan log detection**

```python
# test/test_maintenance_service.py
"""Tests for arm/services/maintenance.py — orphan detection and cleanup."""
import os
import unittest.mock

import pytest

from arm.database import db
from arm.models.job import Job


@pytest.fixture
def tmp_logs(tmp_path):
    """Create a temporary log directory with test log files."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "orphan1.log").write_text("log content")
    (log_dir / "orphan2.log").write_text("log content")
    (log_dir / "referenced.log").write_text("log content")
    (log_dir / "not-a-log.txt").write_text("ignored")
    return log_dir


class TestOrphanLogDetection:
    def test_finds_orphan_logs(self, app_context, sample_job, tmp_logs):
        """Logs not referenced by any job are orphans."""
        sample_job.logfile = "referenced.log"
        db.session.commit()

        with unittest.mock.patch("arm.config.config.arm_config", {"LOGPATH": str(tmp_logs)}):
            from arm.services.maintenance import get_orphan_logs
            result = get_orphan_logs()

        assert result["root"] == str(tmp_logs)
        names = [f["relative_path"] for f in result["files"]]
        assert "orphan1.log" in names
        assert "orphan2.log" in names
        assert "referenced.log" not in names
        assert "not-a-log.txt" not in names

    def test_returns_file_sizes(self, app_context, sample_job, tmp_logs):
        sample_job.logfile = "referenced.log"
        db.session.commit()

        with unittest.mock.patch("arm.config.config.arm_config", {"LOGPATH": str(tmp_logs)}):
            from arm.services.maintenance import get_orphan_logs
            result = get_orphan_logs()

        for f in result["files"]:
            assert isinstance(f["size_bytes"], int)
            assert f["size_bytes"] > 0
        assert isinstance(result["total_size_bytes"], int)

    def test_empty_log_dir(self, app_context, tmp_path):
        log_dir = tmp_path / "empty_logs"
        log_dir.mkdir()
        with unittest.mock.patch("arm.config.config.arm_config", {"LOGPATH": str(log_dir)}):
            from arm.services.maintenance import get_orphan_logs
            result = get_orphan_logs()
        assert result["files"] == []
        assert result["total_size_bytes"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/src/automatic-ripping-machine-neu && python -m pytest test/test_maintenance_service.py -v -x`
Expected: FAIL — `ModuleNotFoundError: No module named 'arm.services.maintenance'`

- [ ] **Step 3: Implement orphan log detection**

```python
# arm/services/maintenance.py
"""Maintenance service — orphan detection and filesystem cleanup."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import arm.config.config as cfg
from arm.database import db
from arm.models.job import Job

log = logging.getLogger(__name__)


def get_orphan_logs() -> dict[str, Any]:
    """Find log files not referenced by any job.

    Scans LOGPATH for *.log files and cross-references against Job.logfile.
    Returns dict with root, total_size_bytes, and files list.
    """
    log_path = Path(cfg.arm_config["LOGPATH"])
    if not log_path.is_dir():
        return {"root": str(log_path), "total_size_bytes": 0, "files": []}

    # Get all logfile references from jobs
    referenced = set()
    for (logfile,) in db.session.query(Job.logfile).filter(Job.logfile.isnot(None)).all():
        referenced.add(logfile)

    orphans = []
    total_size = 0
    for f in sorted(log_path.glob("*.log")):
        if f.name not in referenced:
            size = f.stat().st_size
            orphans.append({
                "path": str(f),
                "relative_path": f.name,
                "size_bytes": size,
            })
            total_size += size

    return {"root": str(log_path), "total_size_bytes": total_size, "files": orphans}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/src/automatic-ripping-machine-neu && python -m pytest test/test_maintenance_service.py::TestOrphanLogDetection -v`
Expected: PASS

- [ ] **Step 5: Write tests for orphan folder detection**

Add to `test/test_maintenance_service.py`:

```python
@pytest.fixture
def tmp_media(tmp_path):
    """Create temporary raw and completed directories with test folders."""
    raw = tmp_path / "raw"
    completed = tmp_path / "completed" / "movies"
    raw.mkdir()
    completed.mkdir(parents=True)
    (raw / "Orphan Movie").mkdir()
    (raw / "Orphan Movie" / "title.mkv").write_bytes(b"\x00" * 1024)
    (raw / "SERIAL_MOM").mkdir()  # matches sample_job.title
    (completed / "Another Orphan").mkdir()
    return {"raw": str(raw), "completed": str(tmp_path / "completed")}


class TestOrphanFolderDetection:
    def test_finds_orphan_folders(self, app_context, sample_job, tmp_media):
        """Folders not matching any job title/label/raw_path are orphans."""
        mock_cfg = {
            "RAW_PATH": tmp_media["raw"],
            "COMPLETED_PATH": tmp_media["completed"],
        }
        with unittest.mock.patch("arm.config.config.arm_config", mock_cfg):
            from arm.services.maintenance import get_orphan_folders
            result = get_orphan_folders()

        names = [f["name"] for f in result["folders"]]
        assert "Orphan Movie" in names
        assert "Another Orphan" in names
        assert "SERIAL_MOM" not in names  # matches sample_job.title

    def test_categorizes_raw_and_completed(self, app_context, sample_job, tmp_media):
        mock_cfg = {
            "RAW_PATH": tmp_media["raw"],
            "COMPLETED_PATH": tmp_media["completed"],
        }
        with unittest.mock.patch("arm.config.config.arm_config", mock_cfg):
            from arm.services.maintenance import get_orphan_folders
            result = get_orphan_folders()

        categories = {f["name"]: f["category"] for f in result["folders"]}
        assert categories.get("Orphan Movie") == "raw"
        assert categories.get("Another Orphan") == "completed"

    def test_computes_folder_sizes(self, app_context, sample_job, tmp_media):
        mock_cfg = {
            "RAW_PATH": tmp_media["raw"],
            "COMPLETED_PATH": tmp_media["completed"],
        }
        with unittest.mock.patch("arm.config.config.arm_config", mock_cfg):
            from arm.services.maintenance import get_orphan_folders
            result = get_orphan_folders()

        orphan_movie = next(f for f in result["folders"] if f["name"] == "Orphan Movie")
        assert orphan_movie["size_bytes"] >= 1024  # has a 1KB file inside
        assert isinstance(result["total_size_bytes"], int)
```

- [ ] **Step 6: Implement orphan folder detection**

Add to `arm/services/maintenance.py`:

```python
def _dir_size(path: Path) -> int:
    """Compute total size of all files in a directory tree."""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat().st_size
            elif entry.is_dir(follow_symlinks=False):
                total += _dir_size(Path(entry.path))
    except PermissionError:
        pass
    return total


def _get_job_references() -> set[str]:
    """Collect all folder name references from jobs (title, label, raw_path basename)."""
    refs: set[str] = set()
    rows = db.session.query(Job.title, Job.label, Job.raw_path, Job.path).all()
    for title, label, raw_path, path in rows:
        if title:
            refs.add(title)
        if label:
            refs.add(label)
        if raw_path:
            refs.add(Path(raw_path).name)
        if path:
            refs.add(Path(path).name)
    return refs


def get_orphan_folders() -> dict[str, Any]:
    """Find folders in RAW_PATH and COMPLETED_PATH not referenced by any job.

    Cross-references directory names against Job.title, Job.label,
    Job.raw_path basename, and Job.path basename.
    """
    raw_path = Path(cfg.arm_config.get("RAW_PATH", ""))
    completed_path = Path(cfg.arm_config.get("COMPLETED_PATH", ""))

    refs = _get_job_references()

    orphans = []
    total_size = 0

    def _scan_dir(root: Path, category: str):
        nonlocal total_size
        if not root.is_dir():
            return
        for entry in sorted(root.iterdir()):
            if entry.is_dir() and entry.name not in refs:
                size = _dir_size(entry)
                orphans.append({
                    "path": str(entry),
                    "name": entry.name,
                    "category": category,
                    "size_bytes": size,
                })
                total_size += size

    _scan_dir(raw_path, "raw")
    # Scan completed subdirectories (completed/movies/, completed/series/, etc.)
    if completed_path.is_dir():
        for subdir in completed_path.iterdir():
            if subdir.is_dir():
                _scan_dir(subdir, "completed")

    return {"total_size_bytes": total_size, "folders": orphans}
```

- [ ] **Step 7: Run all maintenance service tests**

Run: `cd ~/src/automatic-ripping-machine-neu && python -m pytest test/test_maintenance_service.py -v`
Expected: All PASS

- [ ] **Step 8: Write tests for counts**

Add to `test/test_maintenance_service.py`:

```python
class TestMaintenanceCounts:
    def test_returns_counts(self, app_context, sample_job, tmp_logs, tmp_media):
        sample_job.logfile = "referenced.log"
        db.session.commit()

        mock_cfg = {
            "LOGPATH": str(tmp_logs),
            "RAW_PATH": tmp_media["raw"],
            "COMPLETED_PATH": tmp_media["completed"],
        }
        with unittest.mock.patch("arm.config.config.arm_config", mock_cfg):
            from arm.services.maintenance import get_counts
            result = get_counts()

        assert result["orphan_logs"] == 2
        assert result["orphan_folders"] >= 2  # Orphan Movie + Another Orphan
```

- [ ] **Step 9: Implement counts**

Add to `arm/services/maintenance.py`:

```python
def get_counts() -> dict[str, int]:
    """Return orphan counts for summary display."""
    logs = get_orphan_logs()
    folders = get_orphan_folders()
    return {
        "orphan_logs": len(logs["files"]),
        "orphan_folders": len(folders["folders"]),
    }
```

- [ ] **Step 10: Run tests and commit**

Run: `cd ~/src/automatic-ripping-machine-neu && python -m pytest test/test_maintenance_service.py -v`
Expected: All PASS

```bash
cd ~/src/automatic-ripping-machine-neu && git add arm/services/maintenance.py test/test_maintenance_service.py
git commit -m "feat: add maintenance service for orphan detection"
```

---

### Task 2: Maintenance Service — Path Safety & Deletion

**Files:**
- Modify: `arm/services/maintenance.py`
- Modify: `test/test_maintenance_service.py`

- [ ] **Step 1: Write tests for path safety and file deletion**

Add to `test/test_maintenance_service.py`:

```python
class TestPathSafetyAndDeletion:
    def test_delete_orphan_log(self, app_context, tmp_logs):
        target = tmp_logs / "orphan1.log"
        assert target.exists()

        with unittest.mock.patch("arm.config.config.arm_config", {"LOGPATH": str(tmp_logs)}):
            from arm.services.maintenance import delete_log
            result = delete_log(str(target))

        assert result["success"] is True
        assert not target.exists()

    def test_reject_path_outside_root(self, app_context, tmp_logs, tmp_path):
        outside = tmp_path / "outside.log"
        outside.write_text("should not delete")

        with unittest.mock.patch("arm.config.config.arm_config", {"LOGPATH": str(tmp_logs)}):
            from arm.services.maintenance import delete_log
            result = delete_log(str(outside))

        assert result["success"] is False
        assert "outside allowed" in result["error"]
        assert outside.exists()

    def test_reject_path_traversal(self, app_context, tmp_logs):
        traversal = str(tmp_logs / ".." / ".." / "etc" / "passwd")
        with unittest.mock.patch("arm.config.config.arm_config", {"LOGPATH": str(tmp_logs)}):
            from arm.services.maintenance import delete_log
            result = delete_log(traversal)

        assert result["success"] is False

    def test_delete_orphan_folder(self, app_context, tmp_media):
        target_path = os.path.join(tmp_media["raw"], "Orphan Movie")
        assert os.path.isdir(target_path)

        mock_cfg = {
            "RAW_PATH": tmp_media["raw"],
            "COMPLETED_PATH": tmp_media["completed"],
        }
        with unittest.mock.patch("arm.config.config.arm_config", mock_cfg):
            from arm.services.maintenance import delete_folder
            result = delete_folder(target_path)

        assert result["success"] is True
        assert not os.path.exists(target_path)

    def test_delete_folder_outside_roots_rejected(self, app_context, tmp_media, tmp_path):
        outside = tmp_path / "outside_dir"
        outside.mkdir()

        mock_cfg = {
            "RAW_PATH": tmp_media["raw"],
            "COMPLETED_PATH": tmp_media["completed"],
        }
        with unittest.mock.patch("arm.config.config.arm_config", mock_cfg):
            from arm.services.maintenance import delete_folder
            result = delete_folder(str(outside))

        assert result["success"] is False
        assert outside.exists()

    def test_bulk_delete_logs(self, app_context, tmp_logs):
        paths = [str(tmp_logs / "orphan1.log"), str(tmp_logs / "orphan2.log"), str(tmp_logs / "nonexistent.log")]

        with unittest.mock.patch("arm.config.config.arm_config", {"LOGPATH": str(tmp_logs)}):
            from arm.services.maintenance import bulk_delete_logs
            result = bulk_delete_logs(paths)

        assert str(tmp_logs / "orphan1.log") in result["removed"]
        assert str(tmp_logs / "orphan2.log") in result["removed"]
        assert len(result["errors"]) == 1  # nonexistent
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/src/automatic-ripping-machine-neu && python -m pytest test/test_maintenance_service.py::TestPathSafetyAndDeletion -v -x`
Expected: FAIL

- [ ] **Step 3: Implement path safety and deletion functions**

Add to `arm/services/maintenance.py`:

```python
import shutil


def _is_path_within(path: Path, root: Path) -> bool:
    """Check if path is contained within root after resolving symlinks."""
    try:
        resolved = path.resolve()
        root_resolved = root.resolve()
        return resolved.is_relative_to(root_resolved)
    except (ValueError, OSError):
        return False


def delete_log(path_str: str) -> dict[str, Any]:
    """Delete a single log file. Path must be within LOGPATH."""
    target = Path(path_str)
    log_root = Path(cfg.arm_config["LOGPATH"])

    if not _is_path_within(target, log_root):
        return {"success": False, "path": path_str, "error": "Path outside allowed root"}

    resolved = target.resolve()
    if not resolved.is_file():
        return {"success": False, "path": path_str, "error": "File not found"}

    try:
        resolved.unlink()
        return {"success": True, "path": path_str}
    except OSError as exc:
        return {"success": False, "path": path_str, "error": str(exc)}


def delete_folder(path_str: str) -> dict[str, Any]:
    """Delete a single folder. Path must be within RAW_PATH or COMPLETED_PATH."""
    target = Path(path_str)
    allowed_roots = [
        Path(cfg.arm_config.get("RAW_PATH", "")),
        Path(cfg.arm_config.get("COMPLETED_PATH", "")),
    ]

    if not any(_is_path_within(target, root) for root in allowed_roots):
        return {"success": False, "path": path_str, "error": "Path outside allowed roots"}

    resolved = target.resolve()
    if not resolved.is_dir():
        return {"success": False, "path": path_str, "error": "Directory not found"}

    try:
        shutil.rmtree(resolved)
        return {"success": True, "path": path_str}
    except OSError as exc:
        return {"success": False, "path": path_str, "error": str(exc)}


def bulk_delete_logs(paths: list[str]) -> dict[str, Any]:
    """Delete multiple log files. Best-effort — continues on failures."""
    removed = []
    errors = []
    for p in paths:
        result = delete_log(p)
        if result["success"]:
            removed.append(p)
        else:
            errors.append(f"{Path(p).name}: {result.get('error', 'unknown')}")
    return {"removed": removed, "errors": errors}


def bulk_delete_folders(paths: list[str]) -> dict[str, Any]:
    """Delete multiple folders. Best-effort — continues on failures."""
    removed = []
    errors = []
    for p in paths:
        result = delete_folder(p)
        if result["success"]:
            removed.append(p)
        else:
            errors.append(f"{Path(p).name}: {result.get('error', 'unknown')}")
    return {"removed": removed, "errors": errors}
```

- [ ] **Step 4: Run tests and commit**

Run: `cd ~/src/automatic-ripping-machine-neu && python -m pytest test/test_maintenance_service.py -v`
Expected: All PASS

```bash
cd ~/src/automatic-ripping-machine-neu && git add arm/services/maintenance.py test/test_maintenance_service.py
git commit -m "feat: add path-safe deletion for orphan logs and folders"
```

---

### Task 3: ARM Maintenance Router

**Files:**
- Create: `arm/api/v1/maintenance.py`
- Modify: `arm/app.py` (line 32 imports, line 43 include_router)
- Modify: `test/conftest.py` (move `tmp_logs` and `tmp_media` fixtures here so they're shared)
- Test: `test/test_maintenance_api.py`

**Note:** Before writing router tests, move the `tmp_logs` and `tmp_media` fixtures from `test/test_maintenance_service.py` to `test/conftest.py` so they're available to both test files.

- [ ] **Step 1: Write router tests**

```python
# test/test_maintenance_api.py
"""Tests for arm/api/v1/maintenance.py — maintenance REST endpoints."""
import unittest.mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from arm.database import db
from arm.models.job import Job


@pytest.fixture
def maint_client(app_context):
    from arm.api.v1.maintenance import router
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as c:
        yield c


class TestMaintenanceCountsEndpoint:
    def test_returns_counts(self, app_context, sample_job, tmp_logs, maint_client):
        sample_job.logfile = "referenced.log"
        db.session.commit()

        mock_cfg = {"LOGPATH": str(tmp_logs), "RAW_PATH": "/nonexistent", "COMPLETED_PATH": "/nonexistent"}
        with unittest.mock.patch("arm.config.config.arm_config", mock_cfg):
            resp = maint_client.get("/api/v1/maintenance/counts")

        assert resp.status_code == 200
        data = resp.json()
        assert "orphan_logs" in data
        assert "orphan_folders" in data


class TestDeleteEndpoints:
    def test_delete_log_success(self, app_context, tmp_logs, maint_client):
        target = tmp_logs / "orphan1.log"
        with unittest.mock.patch("arm.config.config.arm_config", {"LOGPATH": str(tmp_logs)}):
            resp = maint_client.post("/api/v1/maintenance/delete-log", json={"path": str(target)})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_delete_log_outside_root(self, app_context, tmp_logs, tmp_path, maint_client):
        outside = tmp_path / "evil.log"
        outside.write_text("x")
        with unittest.mock.patch("arm.config.config.arm_config", {"LOGPATH": str(tmp_logs)}):
            resp = maint_client.post("/api/v1/maintenance/delete-log", json={"path": str(outside)})
        assert resp.status_code == 403

    def test_delete_folder_success(self, app_context, tmp_media, maint_client):
        target = os.path.join(tmp_media["raw"], "Orphan Movie")
        mock_cfg = {"RAW_PATH": tmp_media["raw"], "COMPLETED_PATH": tmp_media["completed"]}
        with unittest.mock.patch("arm.config.config.arm_config", mock_cfg):
            resp = maint_client.post("/api/v1/maintenance/delete-folder", json={"path": target})
        assert resp.status_code == 200
        assert resp.json()["success"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/src/automatic-ripping-machine-neu && python -m pytest test/test_maintenance_api.py -v -x`
Expected: FAIL

- [ ] **Step 3: Implement the maintenance router**

```python
# arm/api/v1/maintenance.py
"""API v1 — Maintenance endpoints for orphan detection and cleanup."""
from fastapi import APIRouter
from pydantic import BaseModel

from arm.services import maintenance as svc

router = APIRouter(prefix="/api/v1", tags=["maintenance"])


class PathRequest(BaseModel):
    path: str


class BulkPathRequest(BaseModel):
    paths: list[str]


@router.get("/maintenance/counts")
def get_counts():
    """Return orphan counts for summary display."""
    return svc.get_counts()


@router.get("/maintenance/orphan-logs")
def get_orphan_logs():
    """List log files not referenced by any job."""
    return svc.get_orphan_logs()


@router.get("/maintenance/orphan-folders")
def get_orphan_folders():
    """List folders in RAW_PATH/COMPLETED_PATH not matching any job."""
    return svc.get_orphan_folders()


@router.post("/maintenance/delete-log")
def delete_log(req: PathRequest):
    result = svc.delete_log(req.path)
    if not result["success"] and "outside" in result.get("error", ""):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail=result["error"])
    return result


@router.post("/maintenance/delete-folder")
def delete_folder(req: PathRequest):
    result = svc.delete_folder(req.path)
    if not result["success"] and "outside" in result.get("error", ""):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail=result["error"])
    return result


@router.post("/maintenance/bulk-delete-logs")
def bulk_delete_logs(req: BulkPathRequest):
    return svc.bulk_delete_logs(req.paths)


@router.post("/maintenance/bulk-delete-folders")
def bulk_delete_folders(req: BulkPathRequest):
    return svc.bulk_delete_folders(req.paths)
```

- [ ] **Step 4: Register the router in app.py**

In `arm/app.py`, add to the import on line 32:

```python
from arm.api.v1 import jobs, logs, metadata, notifications, settings, system, drives, files, setup, folder, maintenance  # noqa: E402
```

Add after line 43:

```python
app.include_router(maintenance.router)
```

- [ ] **Step 5: Run tests and commit**

Run: `cd ~/src/automatic-ripping-machine-neu && python -m pytest test/test_maintenance_api.py test/test_maintenance_service.py -v`
Expected: All PASS

```bash
cd ~/src/automatic-ripping-machine-neu && git add arm/api/v1/maintenance.py arm/services/maintenance.py arm/app.py test/test_maintenance_api.py
git commit -m "feat: add maintenance REST endpoints for orphan detection and cleanup"
```

---

### Task 4: ARM — Track Update Endpoint

**Files:**
- Modify: `arm/api/v1/jobs.py`
- Modify: `test/test_jobs_api.py`

The ARM backend already has `PATCH /api/v1/jobs/{job_id}/transcode-config` (line 512 of `arm/api/v1/jobs.py`). We only need to add the track-fields PATCH endpoint. The UI will proxy to the existing `transcode-config` path.

- [ ] **Step 1: Add `job_with_tracks` fixture to `test/test_jobs_api.py`**

The fixture already exists in the file but verify it's present. If not, add it after the `client` fixture:

```python
@pytest.fixture
def job_with_tracks(sample_job):
    """Create a job with several tracks for testing."""
    t1 = Track(sample_job.job_id, '1', 3600, '16:9', 24.0, False, 'makemkv',
               'title_t00.mkv', 'title_t00.mkv', chapters=20, filesize=5000000)
    t2 = Track(sample_job.job_id, '2', 1800, '16:9', 24.0, False, 'makemkv',
               'title_t01.mkv', 'title_t01.mkv', chapters=10, filesize=2500000)
    t3 = Track(sample_job.job_id, '3', 600, '16:9', 24.0, False, 'makemkv',
               'title_t02.mkv', 'title_t02.mkv', chapters=5, filesize=800000)
    db.session.add_all([t1, t2, t3])
    db.session.commit()
    db.session.refresh(sample_job)
    return sample_job, [t1, t2, t3]
```

- [ ] **Step 2: Write tests for the track-fields PATCH endpoint**

Add to `test/test_jobs_api.py`:

```python
class TestTrackFieldUpdates:
    """Test PATCH /api/v1/jobs/{job_id}/tracks/{track_id}."""

    def test_patch_track_enabled(self, app_context, job_with_tracks, client):
        job, tracks = job_with_tracks
        resp = client.patch(
            f"/api/v1/jobs/{job.job_id}/tracks/{tracks[0].track_id}",
            json={"enabled": False},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_patch_track_invalid_field(self, app_context, job_with_tracks, client):
        job, tracks = job_with_tracks
        resp = client.patch(
            f"/api/v1/jobs/{job.job_id}/tracks/{tracks[0].track_id}",
            json={"bad_field": True},
        )
        assert resp.status_code == 400

    def test_patch_track_not_found(self, app_context, sample_job, client):
        resp = client.patch(
            f"/api/v1/jobs/{sample_job.job_id}/tracks/99999",
            json={"enabled": True},
        )
        assert resp.status_code == 404
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd ~/src/automatic-ripping-machine-neu && python -m pytest test/test_jobs_api.py::TestTrackFieldUpdates -v -x`
Expected: FAIL — endpoint doesn't exist yet

- [ ] **Step 4: Implement the track-fields PATCH endpoint**

Add the editable fields constant and endpoint to `arm/api/v1/jobs.py`:

```python
_TRACK_EDITABLE_FIELDS = {"enabled": bool, "filename": str, "ripped": bool}


@router.patch('/jobs/{job_id}/tracks/{track_id}')
def update_track_fields(job_id: int, track_id: int, body: dict):
    """Update editable fields (enabled, filename, ripped) on a track."""
    invalid = set(body.keys()) - _TRACK_EDITABLE_FIELDS.keys()
    if invalid:
        return JSONResponse({"success": False, "error": f"Unknown fields: {', '.join(sorted(invalid))}"}, status_code=400)
    if not body:
        return JSONResponse({"success": False, "error": "No fields to update"}, status_code=400)

    clean = {}
    for key, value in body.items():
        expected = _TRACK_EDITABLE_FIELDS[key]
        if expected is bool:
            if isinstance(value, bool):
                clean[key] = value
            elif isinstance(value, str):
                clean[key] = value.lower() in ("true", "1", "yes")
            else:
                clean[key] = bool(value)
        else:
            clean[key] = str(value)

    track = Track.query.filter_by(track_id=track_id, job_id=job_id).first()
    if not track:
        return JSONResponse({"success": False, "error": "Track not found"}, status_code=404)

    for key, value in clean.items():
        setattr(track, key, value)
    db.session.commit()
    return {"success": True, "job_id": job_id, "track_id": track_id, "updated": clean}
```

- [ ] **Step 5: Run tests and commit**

Run: `cd ~/src/automatic-ripping-machine-neu && python -m pytest test/test_jobs_api.py -v`
Expected: All PASS

```bash
cd ~/src/automatic-ripping-machine-neu && git add arm/api/v1/jobs.py test/test_jobs_api.py
git commit -m "feat: add track-fields PATCH endpoint"
```

---

## Phase 2: UI Backend — Proxy Layer & Local Operations

All tasks in this phase are in `~/src/automatic-ripping-machine-ui`.

### Task 5: arm_client — Maintenance Proxy Functions

**Files:**
- Modify: `backend/services/arm_client.py`
- Test: `frontend/src/lib/__tests__/maintenance-api.test.ts` (later, in Phase 3)

- [ ] **Step 1: Add maintenance proxy functions to arm_client**

Add to the end of `backend/services/arm_client.py`:

```python
# --- Maintenance ---

async def get_maintenance_counts() -> dict[str, Any] | None:
    """Get orphan counts from ARM."""
    return await _request("GET", "/api/v1/maintenance/counts")


async def get_orphan_logs() -> dict[str, Any] | None:
    """Get orphan log files from ARM."""
    return await _request("GET", "/api/v1/maintenance/orphan-logs")


async def get_orphan_folders() -> dict[str, Any] | None:
    """Get orphan folders from ARM."""
    return await _request("GET", "/api/v1/maintenance/orphan-folders")


async def delete_orphan_log(path: str) -> dict[str, Any] | None:
    """Delete a single orphan log file via ARM."""
    return await _request("POST", "/api/v1/maintenance/delete-log", json={"path": path})


async def delete_orphan_folder(path: str) -> dict[str, Any] | None:
    """Delete a single orphan folder via ARM."""
    return await _request("POST", "/api/v1/maintenance/delete-folder", json={"path": path})


async def bulk_delete_logs(paths: list[str]) -> dict[str, Any] | None:
    """Bulk delete orphan log files via ARM."""
    return await _request("POST", "/api/v1/maintenance/bulk-delete-logs", json={"paths": paths})


async def bulk_delete_folders(paths: list[str]) -> dict[str, Any] | None:
    """Bulk delete orphan folders via ARM."""
    return await _request("POST", "/api/v1/maintenance/bulk-delete-folders", json={"paths": paths})


# --- Architecture debt fix: proxy these through ARM ---

async def update_transcode_overrides(job_id: int, overrides: dict) -> dict[str, Any] | None:
    """Update per-job transcode overrides via ARM (existing endpoint)."""
    return await _request("PATCH", f"/api/v1/jobs/{job_id}/transcode-config", json=overrides)


async def update_track_fields(job_id: int, track_id: int, fields: dict) -> dict[str, Any] | None:
    """Update track fields via ARM."""
    return await _request("PATCH", f"/api/v1/jobs/{job_id}/tracks/{track_id}", json=fields)
```

- [ ] **Step 2: Commit**

```bash
cd ~/src/automatic-ripping-machine-ui && git add backend/services/arm_client.py
git commit -m "feat: add maintenance and arch-debt proxy functions to arm_client"
```

---

### Task 6: arm_db — Notification Cleanup Functions

**Files:**
- Modify: `backend/services/arm_db.py`

- [ ] **Step 1: Add notification cleanup functions**

Add after the existing `get_notification_count()` function (around line 296) in `backend/services/arm_db.py`:

```python
def get_cleared_notification_count() -> int:
    """Count notifications marked as cleared."""
    try:
        with get_session() as session:
            stmt = select(func.count()).select_from(Notifications).where(
                Notifications.cleared == True  # noqa: E712
            )
            return session.scalar(stmt) or 0
    except Exception:
        return 0


def dismiss_all_notifications() -> int:
    """Mark all unseen notifications as seen. Returns count affected."""
    try:
        with get_rw_session() as session:
            stmt = (
                update(Notifications)
                .where(Notifications.seen == False)  # noqa: E712
                .values(seen=True)
            )
            result = session.execute(stmt)
            session.commit()
            return result.rowcount
    except Exception:
        log.exception("Failed to dismiss all notifications")
        return 0


def purge_cleared_notifications() -> int:
    """Hard-delete all cleared notifications. Returns count deleted."""
    try:
        with get_rw_session() as session:
            stmt = delete(Notifications).where(
                Notifications.cleared == True  # noqa: E712
            )
            result = session.execute(stmt)
            session.commit()
            return result.rowcount
    except Exception:
        log.exception("Failed to purge cleared notifications")
        return 0
```

Also add `update` and `delete` to the SQLAlchemy imports at the top of the file if not already there:

```python
from sqlalchemy import select, func, update, delete
```

- [ ] **Step 2: Commit**

```bash
cd ~/src/automatic-ripping-machine-ui && git add backend/services/arm_db.py
git commit -m "feat: add notification dismiss-all and purge functions to arm_db"
```

---

### Task 7: Maintenance Router

**Files:**
- Create: `backend/routers/maintenance.py`
- Modify: `backend/main.py` (add import + include_router)

- [ ] **Step 1: Create the maintenance router**

```python
# backend/routers/maintenance.py
"""Maintenance endpoints — orchestrates ARM proxy, notifications, and transcoder cleanup."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services import arm_client, arm_db, transcoder_client

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["maintenance"])

_ARM_UNREACHABLE = "ARM web UI is unreachable"


class PathRequest(BaseModel):
    path: str


class BulkPathRequest(BaseModel):
    paths: list[str]


def _check_arm(result: dict[str, Any] | None) -> dict[str, Any]:
    if result is None:
        raise HTTPException(status_code=503, detail=_ARM_UNREACHABLE)
    return result


@router.get("/maintenance/summary")
async def get_summary():
    """Aggregate counts from ARM, notifications DB, and transcoder."""

    async def _arm_counts():
        return await arm_client.get_maintenance_counts()

    async def _transcoder_counts():
        completed = await transcoder_client.get_jobs(status="completed", limit=1)
        failed = await transcoder_client.get_jobs(status="failed", limit=1)
        if completed is None and failed is None:
            return None
        total = 0
        if completed and "total" in completed:
            total += completed["total"]
        if failed and "total" in failed:
            total += failed["total"]
        return total

    arm_task = asyncio.create_task(_arm_counts())
    tc_task = asyncio.create_task(_transcoder_counts())

    arm_counts = await arm_task
    tc_count = await tc_task

    return {
        "orphan_logs": arm_counts.get("orphan_logs") if arm_counts else None,
        "orphan_folders": arm_counts.get("orphan_folders") if arm_counts else None,
        "unseen_notifications": arm_db.get_notification_count(),
        "cleared_notifications": arm_db.get_cleared_notification_count(),
        "stale_transcoder_jobs": tc_count,
    }


@router.get("/maintenance/orphan-logs")
async def get_orphan_logs():
    return _check_arm(await arm_client.get_orphan_logs())


@router.get("/maintenance/orphan-folders")
async def get_orphan_folders():
    return _check_arm(await arm_client.get_orphan_folders())


@router.post("/maintenance/delete-log")
async def delete_log(req: PathRequest):
    return _check_arm(await arm_client.delete_orphan_log(req.path))


@router.post("/maintenance/delete-folder")
async def delete_folder(req: PathRequest):
    return _check_arm(await arm_client.delete_orphan_folder(req.path))


@router.post("/maintenance/bulk-delete-logs")
async def bulk_delete_logs(req: BulkPathRequest):
    return _check_arm(await arm_client.bulk_delete_logs(req.paths))


@router.post("/maintenance/bulk-delete-folders")
async def bulk_delete_folders(req: BulkPathRequest):
    return _check_arm(await arm_client.bulk_delete_folders(req.paths))


@router.post("/maintenance/dismiss-all-notifications")
async def dismiss_all_notifications():
    count = arm_db.dismiss_all_notifications()
    return {"success": True, "count": count}


@router.post("/maintenance/purge-notifications")
async def purge_notifications():
    count = arm_db.purge_cleared_notifications()
    return {"success": True, "count": count}


@router.post("/maintenance/cleanup-transcoder")
async def cleanup_transcoder():
    """Delete completed and failed transcoder jobs. Paginates through all results."""
    deleted = 0
    errors: list[str] = []

    for status in ("completed", "failed"):
        offset = 0
        while True:
            page = await transcoder_client.get_jobs(status=status, limit=50, offset=offset)
            if page is None:
                errors.append(f"Transcoder unreachable while fetching {status} jobs")
                break
            jobs = page.get("jobs", [])
            if not jobs:
                break
            for job in jobs:
                job_id = job.get("id") or job.get("job_id")
                if job_id and await transcoder_client.delete_job(job_id):
                    deleted += 1
                else:
                    errors.append(f"Failed to delete transcoder job {job_id}")
            offset += len(jobs)
            if offset >= page.get("total", 0):
                break

    return {"success": True, "deleted": deleted, "errors": errors}
```

- [ ] **Step 2: Register the router in main.py**

In `backend/main.py`, add to the imports (around line 15) and include_router (after line 63):

Add import:
```python
from backend.routers import maintenance
```

Add registration:
```python
app.include_router(maintenance.router)
```

- [ ] **Step 3: Commit**

```bash
cd ~/src/automatic-ripping-machine-ui && git add backend/routers/maintenance.py backend/main.py
git commit -m "feat: add maintenance router with ARM proxy, notification, and transcoder cleanup"
```

---

### Task 8: Architecture Debt Fix — Proxy DB Writes Through ARM

**Files:**
- Modify: `backend/routers/jobs.py` (lines 250-277)

- [ ] **Step 1: Refactor transcode-config endpoint**

Replace lines 250-262 in `backend/routers/jobs.py`:

```python
@router.patch("/jobs/{job_id}/transcode-config", responses={400: {"description": "Invalid request"}, 404: {"description": _JOB_NOT_FOUND}, 502: {}, 503: {}})
async def update_transcode_config(job_id: int, request: Request):
    """Set per-job transcode override settings (proxied to ARM)."""
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")
    result = await arm_client.update_transcode_overrides(job_id, body)
    if result is None:
        raise HTTPException(status_code=503, detail="ARM web UI is unreachable")
    if isinstance(result, dict) and result.get("success") is False:
        detail = result.get("error") or result.get("detail") or "Action failed"
        status = 404 if "not found" in detail.lower() else 502
        raise HTTPException(status_code=status, detail=detail)
    return result
```

- [ ] **Step 2: Refactor track-fields endpoint**

Replace lines 265-277:

```python
@router.patch("/jobs/{job_id}/tracks/{track_id}", responses={400: {"description": "Invalid request"}, 404: {"description": "Track not found"}, 502: {}, 503: {}})
async def update_track_fields(job_id: int, track_id: int, request: Request):
    """Update editable fields (enabled, filename, ripped) on a track (proxied to ARM)."""
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")
    result = await arm_client.update_track_fields(job_id, track_id, body)
    if result is None:
        raise HTTPException(status_code=503, detail="ARM web UI is unreachable")
    if isinstance(result, dict) and result.get("success") is False:
        detail = result.get("error") or result.get("detail") or "Action failed"
        status = 404 if "not found" in detail.lower() else 502
        raise HTTPException(status_code=status, detail=detail)
    return result
```

- [ ] **Step 3: Remove unused arm_db imports if no longer needed**

Check if `arm_db.update_job_transcode_overrides` and `arm_db.update_track_fields` are still called elsewhere in `jobs.py`. If not, the `arm_db` import is still needed for other functions in the file (e.g., `get_job`, `get_jobs_paginated_response`), so leave the import but the two functions in `arm_db.py` can stay (they may still be useful as utilities, and removing them could break tests).

- [ ] **Step 4: Commit**

```bash
cd ~/src/automatic-ripping-machine-ui && git add backend/routers/jobs.py
git commit -m "fix: proxy transcode-overrides and track-fields through ARM instead of direct DB"
```

---

## Phase 3: Frontend

All tasks in this phase are in `~/src/automatic-ripping-machine-ui/frontend`.

### Task 9: Maintenance API Client

**Files:**
- Create: `frontend/src/lib/api/maintenance.ts`
- Create: `frontend/src/lib/__tests__/maintenance-api.test.ts`

- [ ] **Step 1: Write API client tests**

```typescript
// frontend/src/lib/__tests__/maintenance-api.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
	fetchSummary,
	fetchOrphanLogs,
	fetchOrphanFolders,
	deleteLog,
	deleteFolder,
	bulkDeleteLogs,
	bulkDeleteFolders,
	dismissAllNotifications,
	purgeNotifications,
	cleanupTranscoder
} from '$lib/api/maintenance';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

function ok(data: unknown) {
	return { ok: true, json: () => Promise.resolve(data) } as Response;
}

beforeEach(() => mockFetch.mockReset());

describe('maintenance API', () => {
	it('fetchSummary calls GET /api/maintenance/summary', async () => {
		const data = { orphan_logs: 3, orphan_folders: 5, unseen_notifications: 12, cleared_notifications: 45, stale_transcoder_jobs: 8 };
		mockFetch.mockResolvedValueOnce(ok(data));
		const result = await fetchSummary();
		expect(result).toEqual(data);
		expect(mockFetch).toHaveBeenCalledWith('/api/maintenance/summary', expect.objectContaining({ headers: expect.objectContaining({ 'Content-Type': 'application/json' }) }));
	});

	it('deleteLog calls POST with path', async () => {
		mockFetch.mockResolvedValueOnce(ok({ success: true }));
		await deleteLog('/tmp/test.log');
		expect(mockFetch).toHaveBeenCalledWith('/api/maintenance/delete-log', expect.objectContaining({ method: 'POST', body: JSON.stringify({ path: '/tmp/test.log' }) }));
	});

	it('bulkDeleteLogs calls POST with paths array', async () => {
		mockFetch.mockResolvedValueOnce(ok({ removed: ['/a.log'], errors: [] }));
		await bulkDeleteLogs(['/a.log', '/b.log']);
		expect(mockFetch).toHaveBeenCalledWith('/api/maintenance/bulk-delete-logs', expect.objectContaining({ method: 'POST', body: JSON.stringify({ paths: ['/a.log', '/b.log'] }) }));
	});

	it('dismissAllNotifications calls POST', async () => {
		mockFetch.mockResolvedValueOnce(ok({ success: true, count: 5 }));
		const result = await dismissAllNotifications();
		expect(result.count).toBe(5);
	});

	it('cleanupTranscoder calls POST', async () => {
		mockFetch.mockResolvedValueOnce(ok({ success: true, deleted: 3, errors: [] }));
		const result = await cleanupTranscoder();
		expect(result.deleted).toBe(3);
	});
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/lib/__tests__/maintenance-api.test.ts`
Expected: FAIL

- [ ] **Step 3: Implement the API client**

```typescript
// frontend/src/lib/api/maintenance.ts
import { apiFetch } from './client';

export interface MaintenanceSummary {
	orphan_logs: number | null;
	orphan_folders: number | null;
	unseen_notifications: number | null;
	cleared_notifications: number | null;
	stale_transcoder_jobs: number | null;
}

export interface OrphanLog {
	path: string;
	relative_path: string;
	size_bytes: number;
}

export interface OrphanFolder {
	path: string;
	name: string;
	category: 'raw' | 'completed';
	size_bytes: number;
}

export interface OrphanLogsResponse {
	root: string;
	total_size_bytes: number;
	files: OrphanLog[];
}

export interface OrphanFoldersResponse {
	total_size_bytes: number;
	folders: OrphanFolder[];
}

export interface BulkDeleteResult {
	removed: string[];
	errors: string[];
}

export function fetchSummary(): Promise<MaintenanceSummary> {
	return apiFetch('/api/maintenance/summary');
}

export function fetchOrphanLogs(): Promise<OrphanLogsResponse> {
	return apiFetch('/api/maintenance/orphan-logs');
}

export function fetchOrphanFolders(): Promise<OrphanFoldersResponse> {
	return apiFetch('/api/maintenance/orphan-folders');
}

export function deleteLog(path: string): Promise<{ success: boolean }> {
	return apiFetch('/api/maintenance/delete-log', { method: 'POST', body: JSON.stringify({ path }) });
}

export function deleteFolder(path: string): Promise<{ success: boolean }> {
	return apiFetch('/api/maintenance/delete-folder', { method: 'POST', body: JSON.stringify({ path }) });
}

export function bulkDeleteLogs(paths: string[]): Promise<BulkDeleteResult> {
	return apiFetch('/api/maintenance/bulk-delete-logs', { method: 'POST', body: JSON.stringify({ paths }) });
}

export function bulkDeleteFolders(paths: string[]): Promise<BulkDeleteResult> {
	return apiFetch('/api/maintenance/bulk-delete-folders', { method: 'POST', body: JSON.stringify({ paths }) });
}

export function dismissAllNotifications(): Promise<{ success: boolean; count: number }> {
	return apiFetch('/api/maintenance/dismiss-all-notifications', { method: 'POST' });
}

export function purgeNotifications(): Promise<{ success: boolean; count: number }> {
	return apiFetch('/api/maintenance/purge-notifications', { method: 'POST' });
}

export function cleanupTranscoder(): Promise<{ success: boolean; deleted: number; errors: string[] }> {
	return apiFetch('/api/maintenance/cleanup-transcoder', { method: 'POST' });
}
```

- [ ] **Step 4: Run tests and commit**

Run: `cd frontend && npx vitest run src/lib/__tests__/maintenance-api.test.ts`
Expected: All PASS

```bash
cd ~/src/automatic-ripping-machine-ui && git add frontend/src/lib/api/maintenance.ts frontend/src/lib/__tests__/maintenance-api.test.ts
git commit -m "feat: add maintenance API client and tests"
```

---

### Task 10: Sidebar Navigation Update

**Files:**
- Modify: `frontend/src/routes/+layout.svelte` (line 69-70, navItems array)

- [ ] **Step 1: Add maintenance nav item**

Insert after the Files entry (line 69) and before Settings (line 70) in the `navItems` array. Use a wrench icon:

```typescript
{ href: '/maintenance', label: 'Maintenance', icon: 'M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0-5.758a3 3 0 10-4.243-4.243 3 3 0 004.243 4.243z' },
```

- [ ] **Step 2: Commit**

```bash
cd ~/src/automatic-ripping-machine-ui && git add frontend/src/routes/+layout.svelte
git commit -m "feat: add Maintenance nav item to sidebar"
```

---

### Task 11: Maintenance Page Component

**Files:**
- Create: `frontend/src/routes/maintenance/+page.svelte`

This is the main UI component. It follows the existing page patterns in the project.

- [ ] **Step 1: Create the maintenance page**

```svelte
<!-- frontend/src/routes/maintenance/+page.svelte -->
<script lang="ts">
	import { onMount } from 'svelte';
	import {
		fetchSummary,
		fetchOrphanLogs,
		fetchOrphanFolders,
		deleteLog,
		deleteFolder,
		bulkDeleteLogs,
		bulkDeleteFolders,
		dismissAllNotifications,
		purgeNotifications,
		cleanupTranscoder,
		type MaintenanceSummary,
		type OrphanLogsResponse,
		type OrphanFoldersResponse
	} from '$lib/api/maintenance';

	let summary = $state<MaintenanceSummary | null>(null);
	let summaryError = $state<string | null>(null);

	// Section expand states
	let logsOpen = $state(false);
	let foldersOpen = $state(false);
	let notificationsOpen = $state(false);
	let transcoderOpen = $state(false);

	// Section data (lazy-loaded)
	let logsData = $state<OrphanLogsResponse | null>(null);
	let foldersData = $state<OrphanFoldersResponse | null>(null);
	let logsLoading = $state(false);
	let foldersLoading = $state(false);

	// Selection state
	let selectedLogs = $state<Set<string>>(new Set());
	let selectedFolders = $state<Set<string>>(new Set());

	// Action state
	let busy = $state(false);
	let feedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);

	// Confirm dialog
	let confirmOpen = $state(false);
	let confirmTitle = $state('');
	let confirmMessage = $state('');
	let confirmAction = $state<(() => Promise<void>) | null>(null);

	function formatBytes(bytes: number): string {
		if (bytes === 0) return '0 B';
		const units = ['B', 'KB', 'MB', 'GB', 'TB'];
		const i = Math.floor(Math.log(bytes) / Math.log(1024));
		return `${(bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0)} ${units[i]}`;
	}

	function showConfirm(title: string, message: string, action: () => Promise<void>) {
		confirmTitle = title;
		confirmMessage = message;
		confirmAction = action;
		confirmOpen = true;
	}

	async function executeConfirmed() {
		confirmOpen = false;
		if (!confirmAction) return;
		busy = true;
		feedback = null;
		try {
			await confirmAction();
		} catch (e) {
			feedback = { type: 'error', message: e instanceof Error ? e.message : 'Action failed' };
		} finally {
			busy = false;
			confirmAction = null;
		}
	}

	async function loadSummary() {
		try {
			summary = await fetchSummary();
			summaryError = null;
		} catch (e) {
			summaryError = e instanceof Error ? e.message : 'Failed to load summary';
		}
	}

	async function loadLogs() {
		logsLoading = true;
		try {
			logsData = await fetchOrphanLogs();
			selectedLogs = new Set();
		} catch { logsData = null; }
		finally { logsLoading = false; }
	}

	async function loadFolders() {
		foldersLoading = true;
		try {
			foldersData = await fetchOrphanFolders();
			selectedFolders = new Set();
		} catch { foldersData = null; }
		finally { foldersLoading = false; }
	}

	function toggleLogsSection() {
		logsOpen = !logsOpen;
		if (logsOpen && !logsData && !logsLoading) loadLogs();
	}

	function toggleFoldersSection() {
		foldersOpen = !foldersOpen;
		if (foldersOpen && !foldersData && !foldersLoading) loadFolders();
	}

	function toggleLogSelection(path: string) {
		const next = new Set(selectedLogs);
		if (next.has(path)) next.delete(path); else next.add(path);
		selectedLogs = next;
	}

	function toggleFolderSelection(path: string) {
		const next = new Set(selectedFolders);
		if (next.has(path)) next.delete(path); else next.add(path);
		selectedFolders = next;
	}

	async function handleDeleteLog(path: string) {
		showConfirm('Delete Log', `Delete ${path.split('/').pop()}?`, async () => {
			await deleteLog(path);
			feedback = { type: 'success', message: 'Log deleted' };
			await loadLogs();
			await loadSummary();
		});
	}

	async function handleDeleteFolder(path: string) {
		const name = path.split('/').pop();
		showConfirm('Delete Folder', `Delete "${name}" and all its contents?`, async () => {
			await deleteFolder(path);
			feedback = { type: 'success', message: `Folder "${name}" deleted` };
			await loadFolders();
			await loadSummary();
		});
	}

	async function handleBulkDeleteLogs() {
		const count = selectedLogs.size;
		showConfirm('Delete Logs', `Delete ${count} selected log file${count !== 1 ? 's' : ''}?`, async () => {
			const result = await bulkDeleteLogs([...selectedLogs]);
			feedback = { type: result.errors.length ? 'error' : 'success', message: `Deleted ${result.removed.length} log${result.removed.length !== 1 ? 's' : ''}${result.errors.length ? `, ${result.errors.length} error(s)` : ''}` };
			await loadLogs();
			await loadSummary();
		});
	}

	async function handleBulkDeleteFolders() {
		const count = selectedFolders.size;
		showConfirm('Delete Folders', `Delete ${count} selected folder${count !== 1 ? 's' : ''} and all their contents?`, async () => {
			const result = await bulkDeleteFolders([...selectedFolders]);
			feedback = { type: result.errors.length ? 'error' : 'success', message: `Deleted ${result.removed.length} folder${result.removed.length !== 1 ? 's' : ''}${result.errors.length ? `, ${result.errors.length} error(s)` : ''}` };
			await loadFolders();
			await loadSummary();
		});
	}

	async function handleDismissNotifications() {
		showConfirm('Dismiss Notifications', 'Mark all unseen notifications as seen?', async () => {
			const result = await dismissAllNotifications();
			feedback = { type: 'success', message: `${result.count} notification${result.count !== 1 ? 's' : ''} dismissed` };
			await loadSummary();
		});
	}

	async function handlePurgeNotifications() {
		showConfirm('Purge Notifications', 'Permanently delete all cleared notifications from the database?', async () => {
			const result = await purgeNotifications();
			feedback = { type: 'success', message: `${result.count} notification${result.count !== 1 ? 's' : ''} purged` };
			await loadSummary();
		});
	}

	async function handleCleanupTranscoder() {
		showConfirm('Clean Up Transcoder', 'Delete all completed and failed transcoder jobs?', async () => {
			const result = await cleanupTranscoder();
			feedback = { type: result.errors.length ? 'error' : 'success', message: `Deleted ${result.deleted} job${result.deleted !== 1 ? 's' : ''}${result.errors.length ? `, ${result.errors.length} error(s)` : ''}` };
			await loadSummary();
		});
	}

	onMount(loadSummary);
</script>

<svelte:head><title>Maintenance — ARM</title></svelte:head>

<div class="mx-auto max-w-4xl p-4">
	<h1 class="mb-4 text-2xl font-bold text-gray-900 dark:text-white">Maintenance</h1>

	<!-- Feedback -->
	{#if feedback}
		<div class="mb-4 rounded-lg px-4 py-2.5 text-sm {feedback.type === 'success' ? 'bg-green-500/10 text-green-700 dark:text-green-400' : 'bg-red-500/10 text-red-700 dark:text-red-400'}">
			{feedback.message}
			<button onclick={() => { feedback = null; }} class="ml-2 opacity-60 hover:opacity-100">✕</button>
		</div>
	{/if}

	{#if summaryError}
		<div class="mb-4 rounded-lg bg-red-500/10 px-4 py-3 text-sm text-red-700 dark:text-red-400">{summaryError}</div>
	{/if}

	<div class="space-y-2">
		<!-- Orphan Logs -->
		<div class="rounded-lg border border-primary/15 dark:border-primary/15">
			<button onclick={toggleLogsSection} class="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-gray-900 transition-colors hover:bg-primary/5 dark:text-white dark:hover:bg-primary/10">
				<div class="flex items-center gap-2">
					<svg class="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
					</svg>
					Orphan Logs
					{#if summary?.orphan_logs != null}
						<span class="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary-text dark:text-primary-text-dark">{summary.orphan_logs}</span>
					{:else if summary?.orphan_logs === null}
						<span class="text-xs text-gray-400">unavailable</span>
					{/if}
				</div>
				<svg class="h-4 w-4 transition-transform {logsOpen ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
				</svg>
			</button>
			{#if logsOpen}
				<div class="border-t border-primary/10 px-4 py-3 dark:border-primary/10">
					{#if logsLoading}
						<p class="text-sm text-gray-400">Loading...</p>
					{:else if logsData && logsData.files.length > 0}
						<div class="mb-2 flex items-center justify-between">
							<span class="text-xs text-gray-500 dark:text-gray-400">{logsData.files.length} file{logsData.files.length !== 1 ? 's' : ''} — {formatBytes(logsData.total_size_bytes)}</span>
							{#if selectedLogs.size > 0}
								<button onclick={handleBulkDeleteLogs} disabled={busy} class="rounded bg-red-500/15 px-2.5 py-1 text-xs font-medium text-red-700 hover:bg-red-500/25 disabled:opacity-50 dark:text-red-400">Delete Selected ({selectedLogs.size})</button>
							{/if}
						</div>
						{#each logsData.files as file}
							<div class="flex items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-primary/5 dark:hover:bg-primary/10">
								<input type="checkbox" checked={selectedLogs.has(file.path)} onchange={() => toggleLogSelection(file.path)} class="h-3.5 w-3.5 rounded border-gray-300 dark:border-gray-600" />
								<span class="flex-1 truncate font-mono text-xs text-gray-700 dark:text-gray-300">{file.relative_path}</span>
								<span class="text-xs text-gray-400">{formatBytes(file.size_bytes)}</span>
								<button onclick={() => handleDeleteLog(file.path)} disabled={busy} class="rounded px-2 py-0.5 text-xs text-red-600 hover:bg-red-500/15 disabled:opacity-50 dark:text-red-400">Delete</button>
							</div>
						{/each}
					{:else}
						<p class="text-sm text-gray-400 dark:text-gray-500">No orphan log files found.</p>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Orphan Folders -->
		<div class="rounded-lg border border-primary/15 dark:border-primary/15">
			<button onclick={toggleFoldersSection} class="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-gray-900 transition-colors hover:bg-primary/5 dark:text-white dark:hover:bg-primary/10">
				<div class="flex items-center gap-2">
					<svg class="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
					</svg>
					Orphan Folders
					{#if summary?.orphan_folders != null}
						<span class="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary-text dark:text-primary-text-dark">{summary.orphan_folders}</span>
					{:else if summary?.orphan_folders === null}
						<span class="text-xs text-gray-400">unavailable</span>
					{/if}
				</div>
				<svg class="h-4 w-4 transition-transform {foldersOpen ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
				</svg>
			</button>
			{#if foldersOpen}
				<div class="border-t border-primary/10 px-4 py-3 dark:border-primary/10">
					{#if foldersLoading}
						<p class="text-sm text-gray-400">Loading...</p>
					{:else if foldersData && foldersData.folders.length > 0}
						<div class="mb-2 flex items-center justify-between">
							<span class="text-xs text-gray-500 dark:text-gray-400">{foldersData.folders.length} folder{foldersData.folders.length !== 1 ? 's' : ''} — {formatBytes(foldersData.total_size_bytes)}</span>
							{#if selectedFolders.size > 0}
								<button onclick={handleBulkDeleteFolders} disabled={busy} class="rounded bg-red-500/15 px-2.5 py-1 text-xs font-medium text-red-700 hover:bg-red-500/25 disabled:opacity-50 dark:text-red-400">Delete Selected ({selectedFolders.size})</button>
							{/if}
						</div>
						{#each foldersData.folders as folder}
							<div class="flex items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-primary/5 dark:hover:bg-primary/10">
								<input type="checkbox" checked={selectedFolders.has(folder.path)} onchange={() => toggleFolderSelection(folder.path)} class="h-3.5 w-3.5 rounded border-gray-300 dark:border-gray-600" />
								<span class="flex-1 truncate text-gray-700 dark:text-gray-300">{folder.name}</span>
								<span class="rounded-full bg-gray-500/10 px-1.5 py-0.5 text-[10px] text-gray-500">{folder.category}</span>
								<span class="text-xs text-gray-400">{formatBytes(folder.size_bytes)}</span>
								<button onclick={() => handleDeleteFolder(folder.path)} disabled={busy} class="rounded px-2 py-0.5 text-xs text-red-600 hover:bg-red-500/15 disabled:opacity-50 dark:text-red-400">Delete</button>
							</div>
						{/each}
					{:else}
						<p class="text-sm text-gray-400 dark:text-gray-500">No orphan folders found.</p>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Notifications -->
		<div class="rounded-lg border border-primary/15 dark:border-primary/15">
			<button onclick={() => { notificationsOpen = !notificationsOpen; }} class="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-gray-900 transition-colors hover:bg-primary/5 dark:text-white dark:hover:bg-primary/10">
				<div class="flex items-center gap-2">
					<svg class="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
					</svg>
					Notifications
					{#if summary}
						{#if summary.unseen_notifications != null || summary.cleared_notifications != null}
							<span class="text-xs text-gray-500 dark:text-gray-400">
								{#if summary.unseen_notifications != null}{summary.unseen_notifications} unseen{/if}{#if summary.unseen_notifications != null && summary.cleared_notifications != null}, {/if}{#if summary.cleared_notifications != null}{summary.cleared_notifications} cleared{/if}
							</span>
						{/if}
					{/if}
				</div>
				<svg class="h-4 w-4 transition-transform {notificationsOpen ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
				</svg>
			</button>
			{#if notificationsOpen}
				<div class="border-t border-primary/10 px-4 py-3 dark:border-primary/10">
					<div class="flex flex-wrap gap-2">
						<button onclick={handleDismissNotifications} disabled={busy || !summary?.unseen_notifications} class="rounded bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary-text transition-colors hover:bg-primary/20 disabled:opacity-50 dark:text-primary-text-dark">
							Dismiss All Unseen{#if summary?.unseen_notifications} ({summary.unseen_notifications}){/if}
						</button>
						<button onclick={handlePurgeNotifications} disabled={busy || !summary?.cleared_notifications} class="rounded bg-red-500/15 px-3 py-1.5 text-xs font-medium text-red-700 transition-colors hover:bg-red-500/25 disabled:opacity-50 dark:text-red-400">
							Purge Cleared{#if summary?.cleared_notifications} ({summary.cleared_notifications}){/if}
						</button>
					</div>
				</div>
			{/if}
		</div>

		<!-- Transcoder Jobs -->
		<div class="rounded-lg border border-primary/15 dark:border-primary/15">
			<button onclick={() => { transcoderOpen = !transcoderOpen; }} class="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-gray-900 transition-colors hover:bg-primary/5 dark:text-white dark:hover:bg-primary/10">
				<div class="flex items-center gap-2">
					<svg class="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
					</svg>
					Transcoder Jobs
					{#if summary?.stale_transcoder_jobs != null}
						<span class="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary-text dark:text-primary-text-dark">{summary.stale_transcoder_jobs}</span>
					{:else if summary?.stale_transcoder_jobs === null}
						<span class="text-xs text-gray-400">unavailable</span>
					{/if}
				</div>
				<svg class="h-4 w-4 transition-transform {transcoderOpen ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
				</svg>
			</button>
			{#if transcoderOpen}
				<div class="border-t border-primary/10 px-4 py-3 dark:border-primary/10">
					<p class="mb-2 text-xs text-gray-500 dark:text-gray-400">Remove completed and failed transcoder jobs from the transcoder database.</p>
					<button onclick={handleCleanupTranscoder} disabled={busy || !summary?.stale_transcoder_jobs} class="rounded bg-red-500/15 px-3 py-1.5 text-xs font-medium text-red-700 transition-colors hover:bg-red-500/25 disabled:opacity-50 dark:text-red-400">
						Clean Up{#if summary?.stale_transcoder_jobs} ({summary.stale_transcoder_jobs} job{summary.stale_transcoder_jobs !== 1 ? 's' : ''}){/if}
					</button>
				</div>
			{/if}
		</div>
	</div>
</div>

<!-- Confirm Dialog -->
{#if confirmOpen}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
		<div class="mx-4 max-w-sm rounded-lg bg-white p-5 shadow-xl dark:bg-gray-800">
			<h3 class="mb-2 font-semibold text-gray-900 dark:text-white">{confirmTitle}</h3>
			<p class="mb-4 text-sm text-gray-600 dark:text-gray-400">{confirmMessage}</p>
			<div class="flex justify-end gap-2">
				<button onclick={() => { confirmOpen = false; confirmAction = null; }} class="rounded px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700">Cancel</button>
				<button onclick={executeConfirmed} class="rounded bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700">Confirm</button>
			</div>
		</div>
	</div>
{/if}
```

- [ ] **Step 2: Commit**

```bash
cd ~/src/automatic-ripping-machine-ui && git add frontend/src/routes/maintenance/+page.svelte
git commit -m "feat: add maintenance page with orphan cleanup, notification, and transcoder sections"
```

---

### Task 12: Frontend Tests & Build Verification

**Files:**
- Create: `frontend/src/routes/maintenance/__tests__/maintenance-page.test.ts`

- [ ] **Step 1: Write page tests**

```typescript
// frontend/src/routes/maintenance/__tests__/maintenance-page.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderComponent, screen, waitFor, fireEvent, cleanup } from '$lib/test-utils';
import MaintenancePage from '../+page.svelte';

vi.mock('$lib/api/maintenance', () => ({
	fetchSummary: vi.fn(() => Promise.resolve({
		orphan_logs: 3,
		orphan_folders: 5,
		unseen_notifications: 12,
		cleared_notifications: 45,
		stale_transcoder_jobs: 8,
	})),
	fetchOrphanLogs: vi.fn(() => Promise.resolve({
		root: '/tmp/logs',
		total_size_bytes: 5242880,
		files: [
			{ path: '/tmp/logs/a.log', relative_path: 'a.log', size_bytes: 1048576 },
			{ path: '/tmp/logs/b.log', relative_path: 'b.log', size_bytes: 4194304 },
		],
	})),
	fetchOrphanFolders: vi.fn(() => Promise.resolve({
		total_size_bytes: 1073741824,
		folders: [{ path: '/raw/Orphan', name: 'Orphan', category: 'raw', size_bytes: 1073741824 }],
	})),
	deleteLog: vi.fn(() => Promise.resolve({ success: true })),
	deleteFolder: vi.fn(() => Promise.resolve({ success: true })),
	bulkDeleteLogs: vi.fn(() => Promise.resolve({ removed: [], errors: [] })),
	bulkDeleteFolders: vi.fn(() => Promise.resolve({ removed: [], errors: [] })),
	dismissAllNotifications: vi.fn(() => Promise.resolve({ success: true, count: 12 })),
	purgeNotifications: vi.fn(() => Promise.resolve({ success: true, count: 45 })),
	cleanupTranscoder: vi.fn(() => Promise.resolve({ success: true, deleted: 8, errors: [] })),
}));

describe('Maintenance Page', () => {
	beforeEach(() => {
		cleanup();
		vi.clearAllMocks();
	});

	it('renders page title and section headers', async () => {
		renderComponent(MaintenancePage);
		await waitFor(() => {
			expect(screen.getByText('Maintenance')).toBeInTheDocument();
		});
		expect(screen.getByText('Orphan Logs')).toBeInTheDocument();
		expect(screen.getByText('Orphan Folders')).toBeInTheDocument();
		expect(screen.getByText('Notifications')).toBeInTheDocument();
		expect(screen.getByText('Transcoder Jobs')).toBeInTheDocument();
	});

	it('shows summary counts after load', async () => {
		renderComponent(MaintenancePage);
		await waitFor(() => {
			expect(screen.getByText('3')).toBeInTheDocument();  // orphan logs
			expect(screen.getByText('5')).toBeInTheDocument();  // orphan folders
			expect(screen.getByText('8')).toBeInTheDocument();  // transcoder jobs
		});
	});

	it('expands orphan logs section and shows files', async () => {
		renderComponent(MaintenancePage);
		await waitFor(() => expect(screen.getByText('3')).toBeInTheDocument());

		await fireEvent.click(screen.getByText('Orphan Logs'));
		await waitFor(() => {
			expect(screen.getByText('a.log')).toBeInTheDocument();
			expect(screen.getByText('b.log')).toBeInTheDocument();
		});
	});
});
```

- [ ] **Step 2: Run page tests**

Run: `cd frontend && npx vitest run src/routes/maintenance/__tests__/maintenance-page.test.ts`
Expected: All PASS

- [ ] **Step 3: Run full frontend test suite**

Run: `cd frontend && npx vitest run`
Expected: All PASS with no regressions

- [ ] **Step 4: Build check**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 5: Commit tests**

```bash
cd ~/src/automatic-ripping-machine-ui && git add frontend/src/routes/maintenance/__tests__/maintenance-page.test.ts
git commit -m "test: add maintenance page tests"
```

---

### Task 13: ARM Backend — Full Test Suite & Build Check

- [ ] **Step 1: Run ARM backend full test suite**

Run: `cd ~/src/automatic-ripping-machine-neu && python -m pytest test/ -v`
Expected: All PASS

- [ ] **Step 2: Fix any issues found**

If tests fail, investigate and fix. Common issues:
- Import order (conftest needs to load before ARM modules)
- Config mock paths not matching

- [ ] **Step 3: Commit any fixes**

```bash
cd ~/src/automatic-ripping-machine-neu && git add -A
git commit -m "fix: address test suite issues from maintenance endpoints"
```
