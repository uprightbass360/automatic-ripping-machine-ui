# Maintenance Page Design

## Overview

Add a standalone `/maintenance` page for system housekeeping: orphan file cleanup, notification management, and transcoder job cleanup. Also fix two architecture debt items where the UI backend writes directly to the ARM database instead of proxying through the ARM API.

Based on features from Jake McBride's PR #88, reimplemented with proper architecture (ARM-first with UI orchestration).

## Problem

- Log files and media folders accumulate on disk after jobs are deleted or fail — no way to find or clean them up
- Notifications pile up forever — `cleared` flag exists but rows are never hard-deleted
- Completed/failed transcoder jobs linger with no bulk cleanup
- Two UI backend endpoints (`transcode-overrides`, `track-fields`) bypass ARM and write directly to the ARM database

## Scope

### In Scope
- Orphan log detection and cleanup (ARM backend)
- Orphan folder detection and cleanup (ARM backend)
- Bulk notification dismiss + hard-delete cleared (UI backend)
- Transcoder job cleanup (UI backend → transcoder API)
- Summary counts endpoint (eager load)
- Architecture fix: proxy transcode overrides through ARM
- Architecture fix: proxy track field updates through ARM
- Frontend `/maintenance` route with sidebar nav

### Out of Scope (Follow-Up)
- DB row counts and health metrics on maintenance page
- Metadata error handling consistency in `arm_client.py`
- Failed job management (belongs on jobs page)
- Drive rescan (already on Settings > Drives tab)
- MakeMKV key check (separate feature)
- Log deletion from logs page (separate feature)

## Architecture

Three layers, each with clear responsibilities:

```
Frontend (/maintenance)
  → UI Backend (/api/maintenance/*)
      → ARM Backend (/api/v1/maintenance/*)  ... orphans, files
      → Transcoder API (/jobs)               ... stale jobs
      → UI Database (notifications)          ... dismiss/purge
```

**ARM backend** owns: orphan detection (cross-reference jobs DB with filesystem), file/folder deletion with path safety validation, counts.

**UI backend** owns: proxying ARM maintenance endpoints, notification cleanup (its own DB), transcoder job cleanup (its own service dependency), aggregating counts from all three sources into a single summary response.

**Frontend** owns: `/maintenance` route, lazy-loading section details, confirm dialogs, auto-refresh after actions.

---

## ARM Backend Changes

**Repo:** `automatic-ripping-machine-neu`
**Branch:** `feat/maintenance`

### New Router: `arm/api/v1/maintenance.py`

#### `GET /api/v1/maintenance/counts`

Returns orphan counts. Used for eager page load summary.

```json
{ "orphan_logs": 3, "orphan_folders": 5 }
```

**Orphan log detection:** Scan `LOGPATH` for `*.log` files. For each file, check if any job in the DB references it via `Job.logfile`. Files with no matching job are orphans.

**Orphan folder detection:** Scan `RAW_PATH` and `COMPLETED_PATH` for directories. For each directory, check if any job references it via `Job.raw_path`, `Job.title` (as a folder name candidate), or `Job.label`. Directories with no matching job are orphans.

#### `GET /api/v1/maintenance/orphan-logs`

Returns full orphan log list with metadata.

```json
{
  "root": "/home/arm/logs",
  "total_size_bytes": 5242880,
  "files": [
    { "path": "/home/arm/logs/old-rip.log", "relative_path": "old-rip.log", "size_bytes": 1048576 }
  ]
}
```

#### `GET /api/v1/maintenance/orphan-folders`

Returns full orphan folder list with metadata.

```json
{
  "total_size_bytes": 50737418240,
  "folders": [
    { "path": "/home/arm/media/raw/Unknown Title", "name": "Unknown Title", "category": "raw", "size_bytes": 26843545600 },
    { "path": "/home/arm/media/completed/movies/Old Movie", "name": "Old Movie", "category": "completed", "size_bytes": 23893872640 }
  ]
}
```

**Folder size:** Walk the directory with `os.scandir` (recursive) to sum file sizes. Do not use `shutil.disk_usage` (it returns filesystem-level stats, not directory size). This may be slow for large folders — consider capping at a reasonable depth or computing asynchronously.

#### `POST /api/v1/maintenance/delete-log`

Delete a single orphan log file.

```json
// Request
{ "path": "/home/arm/logs/old-rip.log" }

// Response
{ "success": true, "path": "/home/arm/logs/old-rip.log" }
```

**Path safety:** Resolve the path and verify it is within `LOGPATH` using `Path.resolve().is_relative_to()`. Reject if not.

#### `POST /api/v1/maintenance/delete-folder`

Delete a single orphan folder.

```json
// Request
{ "path": "/home/arm/media/raw/Unknown Title" }

// Response
{ "success": true, "path": "/home/arm/media/raw/Unknown Title" }
```

**Path safety:** Resolve and verify the path is within `RAW_PATH` or `COMPLETED_PATH`. Use `shutil.rmtree` for deletion.

#### `POST /api/v1/maintenance/bulk-delete-logs`

Delete multiple orphan log files in one call.

```json
// Request
{ "paths": ["/home/arm/logs/a.log", "/home/arm/logs/b.log"] }

// Response
{ "removed": ["/home/arm/logs/a.log"], "errors": ["b.log: not found"] }
```

Best-effort — continues on individual failures, reports results per item.

#### `POST /api/v1/maintenance/bulk-delete-folders`

Delete multiple orphan folders in one call.

```json
// Request
{ "paths": ["/home/arm/media/raw/Foo", "/home/arm/media/raw/Bar"] }

// Response
{ "removed": ["/home/arm/media/raw/Foo"], "errors": ["Bar: permission denied"] }
```

### New Proxy Endpoints (Architecture Debt Fix)

#### `PATCH /api/v1/jobs/{job_id}/transcode-overrides`

Update transcode configuration overrides for a job.

```json
// Request
{ "preset": "H.265 MKV 1080p30", "video_codec": "hevc_nvenc" }

// Response
{ "success": true, "job_id": 123 }
```

Writes to `Job.transcode_overrides` JSON field.

#### `PATCH /api/v1/jobs/{job_id}/tracks/{track_id}`

Update track-level fields.

```json
// Request
{ "enabled": false, "filename": "new-name.mkv" }

// Response
{ "success": true, "job_id": 123, "track_id": 456 }
```

Allowed fields: `enabled` (bool), `filename` (str), `ripped` (bool).

### Path Safety Module

Create a shared utility (e.g., `arm/services/path_safety.py` or inline in the maintenance service) with:

- **`is_path_within(path: Path, root: Path) -> bool`** — resolves both paths and checks containment
- **`delete_file_safe(path: Path, allowed_roots: list[Path]) -> DeleteResult`** — validates and deletes a file
- **`delete_dir_safe(path: Path, allowed_roots: list[Path]) -> DeleteResult`** — validates and deletes a directory with `shutil.rmtree`

`DeleteResult` is a simple dataclass: `success: bool`, `path: str`, `error: str | None`.

---

## UI Backend Changes

**Repo:** `automatic-ripping-machine-ui`
**Branch:** `feat/jake-maintenance`

### New Router: `backend/routers/maintenance.py`

#### `GET /api/maintenance/summary`

Aggregates counts from all three sources in parallel.

```json
{
  "orphan_logs": 3,
  "orphan_folders": 5,
  "unseen_notifications": 12,
  "cleared_notifications": 45,
  "stale_transcoder_jobs": 8
}
```

Implementation: `asyncio.gather` ARM counts + notification counts (DB query) + transcoder job counts. If ARM or transcoder is unreachable, return `null` for those fields.

**Notification counts:** Query `arm_db` for `COUNT(*) WHERE seen = False` and `COUNT(*) WHERE cleared = True`.

**Transcoder job counts:** Call `transcoder_client.get_jobs(status="completed")` + `get_jobs(status="failed")` and sum the totals. If transcoder is unreachable, return `null`.

#### `GET /api/maintenance/orphan-logs`

Proxy to ARM `GET /api/v1/maintenance/orphan-logs`.

#### `GET /api/maintenance/orphan-folders`

Proxy to ARM `GET /api/v1/maintenance/orphan-folders`.

#### `POST /api/maintenance/delete-log`

Proxy to ARM `POST /api/v1/maintenance/delete-log`.

#### `POST /api/maintenance/delete-folder`

Proxy to ARM `POST /api/v1/maintenance/delete-folder`.

#### `POST /api/maintenance/bulk-delete-logs`

Proxy to ARM `POST /api/v1/maintenance/bulk-delete-logs`.

#### `POST /api/maintenance/bulk-delete-folders`

Proxy to ARM `POST /api/v1/maintenance/bulk-delete-folders`.

#### `POST /api/maintenance/dismiss-all-notifications`

Bulk dismiss all unseen notifications. Queries the UI's ARM database directly (notifications are read from the shared ARM DB).

Implementation: `UPDATE notifications SET seen = True WHERE seen = False`.

Returns `{ "success": true, "count": 12 }`.

#### `POST /api/maintenance/purge-notifications`

Hard-delete all cleared notifications from the database.

Implementation: `DELETE FROM notifications WHERE cleared = True`.

Returns `{ "success": true, "count": 45 }`.

#### `POST /api/maintenance/cleanup-transcoder`

Delete completed and failed transcoder jobs.

Implementation:
1. Call `transcoder_client.get_jobs(status="completed")` and `get_jobs(status="failed")`, paginating through all results (default limit is 50 per call — loop until all pages consumed)
2. For each job, call `transcoder_client.delete_job(job_id)`
3. Return `{ "success": true, "deleted": 8, "errors": [] }`

Best-effort — continues on individual failures.

### Architecture Debt Fix: `backend/routers/jobs.py`

#### `PATCH /jobs/{job_id}/transcode-config`

Change from direct `arm_db.update_job_transcode_overrides()` call to `arm_client` proxy call to the new ARM endpoint `PATCH /api/v1/jobs/{job_id}/transcode-overrides`.

#### `PATCH /jobs/{job_id}/tracks/{track_id}`

Change from direct `arm_db.update_track_fields()` call to `arm_client` proxy call to the new ARM endpoint `PATCH /api/v1/jobs/{job_id}/tracks/{track_id}`.

### New `arm_client` Functions

Add to `backend/services/arm_client.py`:

```python
async def get_maintenance_counts() -> dict[str, Any] | None
async def get_orphan_logs() -> dict[str, Any] | None
async def get_orphan_folders() -> dict[str, Any] | None
async def delete_orphan_log(path: str) -> dict[str, Any] | None
async def delete_orphan_folder(path: str) -> dict[str, Any] | None
async def bulk_delete_logs(paths: list[str]) -> dict[str, Any] | None
async def bulk_delete_folders(paths: list[str]) -> dict[str, Any] | None
async def update_transcode_overrides(job_id: int, overrides: dict) -> dict[str, Any] | None
async def update_track_fields(job_id: int, track_id: int, fields: dict) -> dict[str, Any] | None
```

### New `arm_db` Functions

Add to `backend/services/arm_db.py`:

```python
def get_unseen_notification_count() -> int
def get_cleared_notification_count() -> int
def dismiss_all_notifications() -> int  # returns count affected
def purge_cleared_notifications() -> int  # returns count deleted
```

---

## Frontend Changes

### New API Client: `frontend/src/lib/api/maintenance.ts`

```typescript
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

export function fetchSummary(): Promise<MaintenanceSummary>;
export function fetchOrphanLogs(): Promise<OrphanLogsResponse>;
export function fetchOrphanFolders(): Promise<OrphanFoldersResponse>;
export function deleteLog(path: string): Promise<{ success: boolean }>;
export function deleteFolder(path: string): Promise<{ success: boolean }>;
export function bulkDeleteLogs(paths: string[]): Promise<{ removed: string[]; errors: string[] }>;
export function bulkDeleteFolders(paths: string[]): Promise<{ removed: string[]; errors: string[] }>;
export function dismissAllNotifications(): Promise<{ success: boolean; count: number }>;
export function purgeNotifications(): Promise<{ success: boolean; count: number }>;
export function cleanupTranscoder(): Promise<{ success: boolean; deleted: number; errors: string[] }>;
```

### New Route: `frontend/src/routes/maintenance/+page.svelte`

Standalone page with four collapsible sections. Each section shows a count badge in the header and lazy-loads details on expand.

**Page structure:**

```
Maintenance (page title)

[Orphan Logs — 3 items, 5.0 MB]          ▸ expand
[Orphan Folders — 5 items, 47.3 GB]      ▸ expand
[Notifications — 12 unseen, 45 cleared]  ▸ expand
[Transcoder Jobs — 8 stale]              ▸ expand
```

**Expanded section example (Orphan Logs):**

```
Orphan Logs — 3 items, 5.0 MB                    [Delete All]  ▾

  ☐ old-rip.log              1.2 MB    [Delete]
  ☐ failed-scan-2026.log     2.3 MB    [Delete]
  ☐ unknown.log              1.5 MB    [Delete]

  [Delete Selected (0)]
```

**Section behaviors:**
- Counts load eagerly via `/api/maintenance/summary` on page mount
- Details lazy-load on first expand via section-specific endpoints
- Confirm dialog before any destructive action
- After any delete action: auto-refresh the section list and page summary counts
- Sections with count 0 or `null` (unreachable service) show appropriate state
- Null counts show "unavailable" instead of a number (service unreachable)
- Checkbox selection for bulk operations
- Size displayed in human-readable format (KB, MB, GB)

**Notification section actions:**
- "Dismiss All Unseen" — marks all unseen as seen
- "Purge Cleared" — hard-deletes all cleared notifications from DB

**Transcoder section:**
- Shows count of completed + failed transcoder jobs
- "Clean Up" button deletes all completed/failed jobs
- No per-item selection needed (transcoder jobs are ephemeral)

### Sidebar Navigation

Add "Maintenance" nav item to `navItems` array in `frontend/src/routes/+layout.svelte`:

```typescript
{ href: '/maintenance', label: 'Maintenance', icon: '...' }
```

Wrench icon. Position after "Files", before "Settings".

### Architecture Debt Fix: `frontend/src/lib/api/jobs.ts`

No frontend changes needed — the API paths stay the same (`/api/jobs/{id}/transcode-config` and `/api/jobs/{id}/tracks/{tid}`). The fix is backend-only (UI backend proxies to ARM instead of direct DB write).

---

## Testing

### ARM Backend
- Test orphan log detection: create log files, some with matching jobs, verify only orphans returned
- Test orphan folder detection: create folders, some with matching jobs, verify only orphans returned
- Test counts endpoint returns correct numbers
- Test delete-log with valid path, path outside allowed root, nonexistent file
- Test delete-folder with valid path, path traversal attempt, nonexistent folder
- Test bulk-delete with mix of valid and invalid paths
- Test transcode-overrides PATCH updates the job record
- Test track-fields PATCH updates the track record with allowed fields only

### UI Backend
- Test summary aggregates ARM counts + notification counts + transcoder counts
- Test summary handles ARM unreachable (returns null for orphan fields)
- Test summary handles transcoder unreachable (returns null for transcoder field)
- Test dismiss-all-notifications updates DB correctly
- Test purge-notifications deletes correct rows
- Test cleanup-transcoder calls delete for each completed/failed job
- Test proxy endpoints forward to ARM correctly
- Test jobs.py transcode-config now calls arm_client instead of arm_db
- Test jobs.py track-fields now calls arm_client instead of arm_db

### Frontend
- Test maintenance page renders with summary counts
- Test sections expand and load detail data
- Test delete actions show confirm dialog
- Test bulk delete with checkbox selection
- Test sections refresh after delete actions
- Test null counts show "unavailable" state
- Test sidebar shows maintenance nav item

---

## Dependencies

No new packages needed in any repo. All required libraries (httpx, SQLAlchemy, shutil, pathlib) are already available.

## Follow-Up Items

- DB row counts and health metrics on maintenance page
- Metadata error handling consistency in `arm_client.py`
- Per-job purge action on jobs page (cascade delete with transcoder cleanup)
- Stale drive bulk cleanup (if needed beyond Settings > Drives)
