# Jobs Page Redesign

## Summary

Redesign the jobs page with a stats bar, pill-based filters, sortable column headers, row checkboxes, and a gear menu for bulk actions (delete/purge). Add backend support for sorting, disc type filtering, time range filtering, job stats counts, and bulk delete/purge operations.

## Changes

### 1. Backend — Sort, Filter, Stats

Add query parameters to `GET /api/jobs`:

- `sort_by` (string, optional): Column to sort by. Allowed values: `title`, `year`, `status`, `video_type`, `disctype`, `start_time`. Default: `start_time`
- `sort_dir` (string, optional): `asc` or `desc`. Default: `desc`
- `disctype` (string, optional): Filter by disc type (`dvd`, `bluray`, `bluray4k`, `music`, `data`)
- `days` (integer, optional): Only return jobs from the last N days

Update `arm_db.get_jobs_paginated()` to accept and apply these parameters.

New endpoint: `GET /api/jobs/stats`

Returns counts by status for the stats bar:

```json
{
  "total": 147,
  "active": 2,
  "success": 128,
  "fail": 12,
  "waiting": 5
}
```

"Active" includes statuses: `active`, `ripping`, `transcoding`. "Waiting" includes `waiting`, `waiting_transcode`. Counts respect the current filters (disctype, video_type, days, search) so the stats bar updates when filters change.

### 2. Backend — Bulk Delete & Purge

New endpoint: `POST /api/jobs/bulk-delete`

Request: `{ "job_ids": [1, 2, 3] }` or `{ "status": "fail" }` (delete all with that status)

Calls `arm_client.delete_job()` for each job. Returns `{ "deleted": 3, "errors": [] }`.

New endpoint: `POST /api/jobs/bulk-purge`

Request: Same as bulk-delete.

Purge = delete job record via ARM + delete log file + delete raw folder. For each job:
1. Read the job to get `logfile` and file paths
2. Delete the job via ARM (`DELETE /api/v1/jobs/{id}`)
3. Delete the log file via maintenance endpoint
4. Delete the raw folder via maintenance endpoint

Returns `{ "purged": 3, "errors": [] }`.

### 3. Frontend — API Client Updates

Update `fetchJobs()` to accept new params: `sort_by`, `sort_dir`, `disctype`, `days`.

Add `fetchJobStats()` function.

Add `bulkDeleteJobs()` and `bulkPurgeJobs()` functions.

### 4. Frontend — Stats Bar

Row of 5 clickable stat cards above filters: Total, Active, Success, Failed, Waiting. Each shows a count with colored accent. Clicking a stat card sets the status filter to that value.

Stats are fetched via `GET /api/jobs/stats` with the current filter params (so counts reflect filtered results). Refreshed when filters change.

### 5. Frontend — Filter Pills

Replace the status and video_type dropdowns with pill button groups:

**Row 1:** Search input | Status pills (All, Active, Success, Failed, Waiting) | Type pills (All, Movie, Series, Music)

**Row 2:** Disc pills (All, Blu-ray, DVD, CD) | Time range dropdown (All Time, Last 7 days, Last 30 days, Last 90 days) | [spacer] | Selection count | Gear menu button

Active pill gets highlighted styling. "All" is the default.

### 6. Frontend — Sortable Column Headers

Column headers for Title, Year, Status, Type, Disc, Started are clickable. Clicking toggles sort direction. Shows ↕ when inactive, ▼ when sorting desc, ▲ when sorting asc. Default sort: Started desc.

Sorting is server-side — clicking a header updates `sort_by`/`sort_dir` state and re-fetches from the API.

### 7. Frontend — Row Checkboxes + Selection

Each row gets a checkbox. Header has a select-all checkbox (selects/deselects all visible rows). Selected job IDs are tracked in a `Set<number>`.

Selected row count shown next to gear button: "N selected".

### 8. Frontend — Gear Menu

A `⚙ Actions ▾` button that opens a dropdown with two sections:

**Selected (N)** — only shown when 1+ jobs are checked:
- Delete Selected — removes job records
- Purge Selected — removes job records + logs + raw files

**Bulk Actions** — always shown:
- Delete All Failed (N jobs)
- Purge All Failed (+ logs & files)
- Delete All Successful (N jobs)

All destructive actions require a confirm dialog before executing. Counts in the menu reflect current data.

### 9. Frontend — Per-Row Actions Update

The existing `JobActions` component already handles Abandon, Delete, Fix Permissions. Add:

- **Purge** button for failed/completed jobs — same as delete but also removes log + raw files

### 10. Follow-up: Job Detail Back Navigation

_Not part of this implementation._ Future enhancement: when navigating to a job detail from `/jobs`, the back button returns to `/jobs`. When arriving from elsewhere (dashboard), back goes to `/`.

## Files Changed

**UI backend:**
- `backend/services/arm_db.py` — add sort_by, sort_dir, disctype, days params to `get_jobs_paginated()`. Add `get_job_stats()`.
- `backend/routers/jobs.py` — add query params to list endpoint. Add stats endpoint. Add bulk-delete and bulk-purge endpoints.
- `backend/models/schemas.py` — add `JobStatsResponse` schema if needed.

**UI frontend:**
- `frontend/src/lib/api/jobs.ts` — add new params, stats function, bulk operations
- `frontend/src/routes/jobs/+page.svelte` — full redesign: stats bar, pill filters, sortable headers, checkboxes, gear menu
- `frontend/src/lib/components/JobRow.svelte` — add checkbox column, purge action
- `frontend/src/lib/components/JobActions.svelte` — add purge button

## Design Constraints

- Sorting is server-side (backend sorts, not frontend)
- Stats bar counts must respect active filters
- Bulk purge may be slow (deletes files) — show progress/feedback
- Confirm dialogs for all destructive bulk actions
- Preserve existing per-row action behavior (abandon, delete, fix perms)
