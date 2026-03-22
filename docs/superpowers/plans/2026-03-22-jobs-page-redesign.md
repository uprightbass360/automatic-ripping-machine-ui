# Jobs Page Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Redesign the jobs page with stats bar, pill filters, sortable columns, row checkboxes, and a gear menu for bulk delete/purge operations.

**Architecture:** UI backend gets new sort/filter/stats params on the jobs endpoint, plus bulk delete/purge endpoints. Frontend is rewritten with stats bar, pill-based filters, sortable headers, checkboxes, and a gear dropdown menu for bulk actions.

**Tech Stack:** Python/FastAPI, SQLAlchemy (UI backend), SvelteKit/Svelte 5, Tailwind CSS 4 (frontend), Vitest + Testing Library

**Spec:** `docs/superpowers/specs/2026-03-22-jobs-page-redesign.md`

**Repo:** `~/src/automatic-ripping-machine-ui` (branch `feat/jake-maintenance`)

---

## Phase 1: Backend — Enhanced Queries, Stats & Bulk Operations

### Task 1: Enhanced Job Listing — Sort, Disc Type, Time Range

**Files:**
- Modify: `backend/services/arm_db.py` (`get_jobs_paginated` and `get_jobs_paginated_response`)
- Modify: `backend/routers/jobs.py` (`list_jobs` endpoint)
- Test: `tests/routers/test_jobs_filtering.py`

- [ ] **Step 1: Write tests for new query parameters**

Tests must use the existing `app_client` + `patch()` pattern (async, module-level functions, mocked DB calls). See `tests/routers/test_jobs.py` for the established pattern.

```python
# tests/routers/test_jobs_filtering.py
"""Tests for enhanced job listing — sort, disc type filter, time range."""
from __future__ import annotations
from unittest.mock import patch
from tests.factories import make_job

_EMPTY = {"jobs": [], "total": 0, "page": 1, "per_page": 25, "pages": 1}


async def test_sort_by_title_asc(app_client):
    with patch("backend.routers.jobs.arm_db.get_jobs_paginated_response", return_value=_EMPTY) as mock_fn:
        resp = await app_client.get("/api/jobs?sort_by=title&sort_dir=asc")
    assert resp.status_code == 200
    mock_fn.assert_called_once_with(1, 25, None, None, None, None, None, "title", "asc")


async def test_sort_by_start_time_desc_is_default(app_client):
    with patch("backend.routers.jobs.arm_db.get_jobs_paginated_response", return_value=_EMPTY) as mock_fn:
        resp = await app_client.get("/api/jobs")
    assert resp.status_code == 200
    mock_fn.assert_called_once_with(1, 25, None, None, None, None, None, None, None)


async def test_filter_by_disctype(app_client):
    with patch("backend.routers.jobs.arm_db.get_jobs_paginated_response", return_value=_EMPTY) as mock_fn:
        resp = await app_client.get("/api/jobs?disctype=dvd")
    assert resp.status_code == 200
    mock_fn.assert_called_once_with(1, 25, None, None, None, "dvd", None, None, None)


async def test_filter_by_days(app_client):
    with patch("backend.routers.jobs.arm_db.get_jobs_paginated_response", return_value=_EMPTY) as mock_fn:
        resp = await app_client.get("/api/jobs?days=7")
    assert resp.status_code == 200
    mock_fn.assert_called_once_with(1, 25, None, None, None, None, 7, None, None)


async def test_invalid_sort_dir_rejected(app_client):
    resp = await app_client.get("/api/jobs?sort_dir=invalid")
    assert resp.status_code == 422
```

**Also update the existing test** in `tests/routers/test_jobs.py` — the assertion at line 40:

```python
# OLD:
mock_fn.assert_called_once_with(3, 10, "active", None, None)
# NEW (5 extra None params for disctype, days, sort_by, sort_dir):
mock_fn.assert_called_once_with(3, 10, "active", None, None, None, None, None, None)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/src/automatic-ripping-machine-ui && python3 -m pytest tests/routers/test_jobs_filtering.py -v -x`
Expected: FAIL — new query params not yet supported

- [ ] **Step 3: Implement enhanced get_jobs_paginated**

In `backend/services/arm_db.py`, replace the existing `get_jobs_paginated` function:

```python
_SORTABLE_COLUMNS = {
    "title": Job.title,
    "year": Job.year,
    "status": Job.status,
    "video_type": Job.video_type,
    "disctype": Job.disctype,
    "start_time": Job.start_time,
}


def get_jobs_paginated(
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
    search: str | None = None,
    video_type: str | None = None,
    disctype: str | None = None,
    days: int | None = None,
    sort_by: str | None = None,
    sort_dir: str | None = None,
) -> tuple[list[Job], int]:
    try:
        with get_session() as session:
            stmt = select(Job)

            if status:
                status_lower = status.lower()
                if status_lower == "active":
                    stmt = stmt.where(func.lower(Job.status).in_(["active", "ripping", "transcoding"]))
                elif status_lower == "waiting":
                    stmt = stmt.where(func.lower(Job.status).in_(["waiting", "waiting_transcode"]))
                else:
                    stmt = stmt.where(func.lower(Job.status) == status_lower)
            if video_type:
                stmt = stmt.where(func.lower(Job.video_type) == video_type.lower())
            if disctype:
                stmt = stmt.where(func.lower(Job.disctype) == disctype.lower())
            if days and days > 0:
                from datetime import datetime, timedelta
                cutoff = datetime.utcnow() - timedelta(days=days)
                stmt = stmt.where(Job.start_time >= cutoff)
            if search:
                pattern = f"%{search}%"
                stmt = stmt.where(
                    or_(
                        Job.title.ilike(pattern),
                        Job.title_auto.ilike(pattern),
                        Job.title_manual.ilike(pattern),
                        Job.label.ilike(pattern),
                    )
                )

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = session.scalar(count_stmt) or 0

            # Sorting
            col = _SORTABLE_COLUMNS.get(sort_by, Job.start_time)
            if sort_dir == "asc":
                stmt = stmt.order_by(col.asc().nulls_last())
            else:
                stmt = stmt.order_by(col.desc().nulls_last())

            stmt = stmt.offset((page - 1) * per_page).limit(per_page)
            jobs = list(session.scalars(stmt).unique().all())

            return jobs, total
    except Exception:
        return [], 0
```

Update `get_jobs_paginated_response` to pass through the new params:

```python
def get_jobs_paginated_response(
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
    search: str | None = None,
    video_type: str | None = None,
    disctype: str | None = None,
    days: int | None = None,
    sort_by: str | None = None,
    sort_dir: str | None = None,
) -> dict:
    jobs, total = get_jobs_paginated(
        page, per_page, status, search, video_type,
        disctype, days, sort_by, sort_dir,
    )
    return {
        "jobs": jobs,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, math.ceil(total / per_page)) if total else 1,
    }
```

Update the `list_jobs` endpoint in `backend/routers/jobs.py`:

```python
@router.get("/jobs", response_model=JobListResponse)
def list_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    status: str | None = None,
    search: str | None = None,
    video_type: str | None = None,
    disctype: str | None = None,
    days: int | None = Query(None, ge=1),
    sort_by: str | None = None,
    sort_dir: str | None = Query(None, pattern="^(asc|desc)$"),
):
    data = arm_db.get_jobs_paginated_response(
        page, per_page, status, search, video_type,
        disctype, days, sort_by, sort_dir,
    )
    return JobListResponse(
        jobs=[JobSchema.model_validate(j) for j in data["jobs"]],
        total=data["total"],
        page=data["page"],
        per_page=data["per_page"],
        pages=data["pages"],
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/src/automatic-ripping-machine-ui && python3 -m pytest tests/routers/test_jobs_filtering.py -v -x`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/arm_db.py backend/routers/jobs.py tests/routers/test_jobs_filtering.py
git commit -m "feat: add sorting, disc type filter, and time range to jobs endpoint"
```

---

### Task 2: Job Stats Endpoint

**Files:**
- Modify: `backend/services/arm_db.py` (add `get_job_stats`)
- Modify: `backend/routers/jobs.py` (add stats endpoint)
- Test: `tests/routers/test_jobs_stats.py`

- [ ] **Step 1: Write tests for stats endpoint**

```python
# tests/routers/test_jobs_stats.py
"""Tests for GET /api/jobs/stats endpoint."""
from __future__ import annotations
from unittest.mock import patch

_STATS = {"total": 10, "active": 2, "success": 5, "fail": 2, "waiting": 1}


async def test_stats_returns_all_fields(app_client):
    with patch("backend.routers.jobs.arm_db.get_job_stats", return_value=_STATS):
        resp = await app_client.get("/api/jobs/stats")
    assert resp.status_code == 200
    data = resp.json()
    for key in ("total", "active", "success", "fail", "waiting"):
        assert key in data


async def test_stats_passes_filters(app_client):
    with patch("backend.routers.jobs.arm_db.get_job_stats", return_value=_STATS) as mock_fn:
        resp = await app_client.get("/api/jobs/stats?disctype=dvd&video_type=movie&days=7")
    assert resp.status_code == 200
    mock_fn.assert_called_once_with(None, "movie", "dvd", 7)


async def test_stats_no_filters(app_client):
    with patch("backend.routers.jobs.arm_db.get_job_stats", return_value=_STATS) as mock_fn:
        resp = await app_client.get("/api/jobs/stats")
    assert resp.status_code == 200
    mock_fn.assert_called_once_with(None, None, None, None)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/src/automatic-ripping-machine-ui && python3 -m pytest tests/routers/test_jobs_stats.py -v -x`
Expected: FAIL — endpoint doesn't exist

- [ ] **Step 3: Implement stats**

Add to `backend/services/arm_db.py`:

```python
_ACTIVE_STATUSES = ["active", "ripping", "transcoding"]
_WAITING_STATUSES = ["waiting", "waiting_transcode"]


def get_job_stats(
    search: str | None = None,
    video_type: str | None = None,
    disctype: str | None = None,
    days: int | None = None,
) -> dict:
    """Return job counts by status category, respecting filters."""
    try:
        with get_session() as session:
            base = select(Job)

            if video_type:
                base = base.where(func.lower(Job.video_type) == video_type.lower())
            if disctype:
                base = base.where(func.lower(Job.disctype) == disctype.lower())
            if days and days > 0:
                from datetime import datetime, timedelta
                cutoff = datetime.utcnow() - timedelta(days=days)
                base = base.where(Job.start_time >= cutoff)
            if search:
                pattern = f"%{search}%"
                base = base.where(
                    or_(
                        Job.title.ilike(pattern),
                        Job.title_auto.ilike(pattern),
                        Job.title_manual.ilike(pattern),
                        Job.label.ilike(pattern),
                    )
                )

            sub = base.subquery()
            total = session.scalar(select(func.count()).select_from(sub)) or 0

            def _count_statuses(statuses: list[str]) -> int:
                q = base.where(func.lower(Job.status).in_(statuses))
                return session.scalar(select(func.count()).select_from(q.subquery())) or 0

            def _count_status(s: str) -> int:
                q = base.where(func.lower(Job.status) == s)
                return session.scalar(select(func.count()).select_from(q.subquery())) or 0

            return {
                "total": total,
                "active": _count_statuses(_ACTIVE_STATUSES),
                "success": _count_status("success"),
                "fail": _count_status("fail"),
                "waiting": _count_statuses(_WAITING_STATUSES),
            }
    except Exception:
        return {"total": 0, "active": 0, "success": 0, "fail": 0, "waiting": 0}
```

Add endpoint to `backend/routers/jobs.py` (before the `get_job` endpoint so it doesn't conflict with `{job_id}` path):

```python
@router.get("/jobs/stats")
def get_job_stats(
    search: str | None = None,
    video_type: str | None = None,
    disctype: str | None = None,
    days: int | None = Query(None, ge=1),
):
    return arm_db.get_job_stats(search, video_type, disctype, days)
```

**Important:** This endpoint MUST be defined before `@router.get("/jobs/{job_id}")` in the file, otherwise FastAPI will try to parse "stats" as a job_id integer and return 422.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/src/automatic-ripping-machine-ui && python3 -m pytest tests/routers/test_jobs_stats.py -v -x`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/arm_db.py backend/routers/jobs.py tests/routers/test_jobs_stats.py
git commit -m "feat: add GET /api/jobs/stats endpoint with filter support"
```

---

### Task 3: Bulk Delete & Purge Endpoints

**Files:**
- Modify: `backend/routers/jobs.py` (add bulk endpoints)
- Test: `tests/routers/test_jobs_bulk.py`

- [ ] **Step 1: Write tests for bulk operations**

```python
# tests/routers/test_jobs_bulk.py
"""Tests for POST /api/jobs/bulk-delete and /api/jobs/bulk-purge."""
from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock, patch
from tests.factories import make_job


async def test_bulk_delete_by_ids(app_client):
    mock_del = AsyncMock(return_value={"success": True})
    with patch("backend.routers.jobs.arm_client.delete_job", mock_del):
        resp = await app_client.post("/api/jobs/bulk-delete", json={"job_ids": [1, 2]})
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 2
    assert mock_del.call_count == 2


async def test_bulk_delete_empty_ids(app_client):
    resp = await app_client.post("/api/jobs/bulk-delete", json={"job_ids": []})
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 0


async def test_bulk_delete_by_status(app_client):
    jobs = [make_job(job_id=i, status="fail") for i in range(1, 4)]
    mock_del = AsyncMock(return_value={"success": True})
    with patch("backend.routers.jobs.arm_db.get_jobs_paginated", return_value=(jobs, 3)), \
         patch("backend.routers.jobs.arm_client.delete_job", mock_del):
        resp = await app_client.post("/api/jobs/bulk-delete", json={"status": "fail"})
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 3


async def test_bulk_purge_by_ids(app_client):
    job_mock = make_job(job_id=1, logfile="test.log")
    mock_del = AsyncMock(return_value={"success": True})
    mock_log = AsyncMock(return_value={"success": True})
    mock_folder = AsyncMock(return_value={"success": True})
    with patch("backend.routers.jobs.arm_db.get_job", return_value=job_mock), \
         patch("backend.routers.jobs.arm_client.delete_job", mock_del), \
         patch("backend.routers.jobs.arm_client.delete_orphan_log", mock_log), \
         patch("backend.routers.jobs.arm_client.delete_orphan_folder", mock_folder):
        resp = await app_client.post("/api/jobs/bulk-purge", json={"job_ids": [1]})
    assert resp.status_code == 200
    assert resp.json()["purged"] == 1


async def test_bulk_purge_empty_ids(app_client):
    resp = await app_client.post("/api/jobs/bulk-purge", json={"job_ids": []})
    assert resp.status_code == 200
    assert resp.json()["purged"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/src/automatic-ripping-machine-ui && python3 -m pytest tests/routers/test_jobs_bulk.py -v -x`
Expected: FAIL — endpoints don't exist

- [ ] **Step 3: Implement bulk endpoints**

Add to `backend/routers/jobs.py`:

```python
from pydantic import BaseModel


class BulkJobRequest(BaseModel):
    job_ids: list[int] | None = None
    status: str | None = None


@router.post("/jobs/bulk-delete")
async def bulk_delete_jobs(req: BulkJobRequest):
    """Delete multiple jobs by ID list or by status."""
    job_ids = _resolve_job_ids(req)
    deleted = 0
    errors: list[str] = []

    for job_id in job_ids:
        result = await arm_client.delete_job(job_id)
        if result is None:
            errors.append(f"ARM unreachable for job {job_id}")
        elif result.get("success") is False:
            errors.append(f"Job {job_id}: {result.get('error', 'delete failed')}")
        else:
            deleted += 1

    return {"deleted": deleted, "errors": errors}


@router.post("/jobs/bulk-purge")
async def bulk_purge_jobs(req: BulkJobRequest):
    """Purge multiple jobs — delete record + log file + raw folder."""
    job_ids = _resolve_job_ids(req)
    purged = 0
    errors: list[str] = []

    for job_id in job_ids:
        # Read job to get logfile and raw path before deleting
        job = arm_db.get_job(job_id)
        logfile = getattr(job, "logfile", None) if job else None
        raw_path = getattr(job, "path", None) if job else None

        # Delete job record via ARM
        result = await arm_client.delete_job(job_id)
        if result is None:
            errors.append(f"ARM unreachable for job {job_id}")
            continue
        if result.get("success") is False:
            errors.append(f"Job {job_id}: {result.get('error', 'delete failed')}")
            continue

        # Best-effort: delete log file and raw folder
        if logfile:
            await arm_client.delete_orphan_log(logfile)
        if raw_path:
            await arm_client.delete_orphan_folder(raw_path)

        purged += 1

    return {"purged": purged, "errors": errors}


def _resolve_job_ids(req: BulkJobRequest) -> list[int]:
    """Resolve request to a list of job IDs."""
    if req.job_ids:
        return req.job_ids
    if req.status:
        jobs, _ = arm_db.get_jobs_paginated(
            page=1, per_page=10000, status=req.status,
        )
        return [j.job_id for j in jobs]
    return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/src/automatic-ripping-machine-ui && python3 -m pytest tests/routers/test_jobs_bulk.py -v -x`
Expected: All PASS

- [ ] **Step 5: Run full backend test suite**

Run: `cd ~/src/automatic-ripping-machine-ui && python3 -m pytest tests/ -x -q`
Expected: All pass, no regressions

- [ ] **Step 6: Commit**

```bash
git add backend/routers/jobs.py tests/routers/test_jobs_bulk.py
git commit -m "feat: add bulk delete and purge endpoints for jobs"
```

---

## Phase 2: Frontend — API Client Updates

### Task 4: Frontend API — New Params, Stats, Bulk Operations

**Files:**
- Modify: `frontend/src/lib/api/jobs.ts`

- [ ] **Step 1: Update fetchJobs and add new functions**

Replace the existing `fetchJobs` function and add new ones in `frontend/src/lib/api/jobs.ts`:

```typescript
export function fetchJobs(params?: {
	page?: number;
	per_page?: number;
	status?: string;
	search?: string;
	video_type?: string;
	disctype?: string;
	days?: number;
	sort_by?: string;
	sort_dir?: string;
}): Promise<JobListResponse> {
	const query = new URLSearchParams();
	if (params?.page) query.set('page', String(params.page));
	if (params?.per_page) query.set('per_page', String(params.per_page));
	if (params?.status) query.set('status', params.status);
	if (params?.search) query.set('search', params.search);
	if (params?.video_type) query.set('video_type', params.video_type);
	if (params?.disctype) query.set('disctype', params.disctype);
	if (params?.days) query.set('days', String(params.days));
	if (params?.sort_by) query.set('sort_by', params.sort_by);
	if (params?.sort_dir) query.set('sort_dir', params.sort_dir);
	const qs = query.toString();
	return apiFetch<JobListResponse>(`/api/jobs${qs ? `?${qs}` : ''}`);
}

export interface JobStats {
	total: number;
	active: number;
	success: number;
	fail: number;
	waiting: number;
}

export function fetchJobStats(params?: {
	search?: string;
	video_type?: string;
	disctype?: string;
	days?: number;
}): Promise<JobStats> {
	const query = new URLSearchParams();
	if (params?.search) query.set('search', params.search);
	if (params?.video_type) query.set('video_type', params.video_type);
	if (params?.disctype) query.set('disctype', params.disctype);
	if (params?.days) query.set('days', String(params.days));
	const qs = query.toString();
	return apiFetch<JobStats>(`/api/jobs/stats${qs ? `?${qs}` : ''}`);
}

export function bulkDeleteJobs(params: { job_ids?: number[]; status?: string }): Promise<{ deleted: number; errors: string[] }> {
	return apiFetch('/api/jobs/bulk-delete', { method: 'POST', body: JSON.stringify(params) });
}

export function bulkPurgeJobs(params: { job_ids?: number[]; status?: string }): Promise<{ purged: number; errors: string[] }> {
	return apiFetch('/api/jobs/bulk-purge', { method: 'POST', body: JSON.stringify(params) });
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/api/jobs.ts
git commit -m "feat: add sort, filter, stats, and bulk operations to jobs API client"
```

---

## Phase 3: Frontend — Page Redesign

### Task 5: JobRow — Add Checkbox + Purge Action

**Files:**
- Modify: `frontend/src/lib/components/JobRow.svelte`
- Modify: `frontend/src/lib/components/JobActions.svelte`

- [ ] **Step 1: Add checkbox to JobRow**

In `frontend/src/lib/components/JobRow.svelte`, add props for checkbox state:

```typescript
interface Props {
    job: Job;
    driveNames?: Record<string, string>;
    onaction?: () => void;
    selected?: boolean;
    onselect?: (jobId: number, selected: boolean) => void;
}

let { job, driveNames = {}, onaction, selected = false, onselect }: Props = $props();
```

Add a checkbox `<td>` as the first cell of the `<tr>`:

```svelte
<td class="px-4 py-3 w-8">
    <input
        type="checkbox"
        checked={selected}
        onchange={() => onselect?.(job.job_id, !selected)}
        class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary dark:border-gray-600 dark:bg-gray-700"
    />
</td>
```

Add subtle highlight when selected — update the `<tr>` class:

```svelte
<tr class="border-b border-primary/20 hover:bg-page dark:border-primary/20 dark:hover:bg-primary/5 {selected ? 'bg-primary/[0.03] dark:bg-primary/[0.06]' : ''}">
```

- [ ] **Step 2: Add purge to JobActions**

In `frontend/src/lib/components/JobActions.svelte`, add purge functionality. Import `bulkPurgeJobs` (for single-job purge, we use the same endpoint with one ID):

Add to imports at top:
```typescript
import { abandonJob, deleteJob, fixJobPermissions } from '$lib/api/jobs';
import { bulkPurgeJobs } from '$lib/api/jobs';
```

Add `canPurge` derived and handler:
```typescript
let canPurge = $derived(statusLower === 'fail' || statusLower === 'success');

async function handlePurge() {
    if (!confirm(`Purge job "${job.title || job.label || job.job_id}"? This will delete the job record, log files, and raw files.`)) return;
    loading = 'purge';
    feedback = null;
    try {
        await bulkPurgeJobs({ job_ids: [job.job_id] });
        feedback = { type: 'success', message: 'Job purged' };
        onaction?.();
    } catch (e) {
        feedback = { type: 'error', message: e instanceof Error ? e.message : 'Failed to purge' };
    } finally {
        loading = null;
        clearFeedback();
    }
}
```

Add the Purge button in the template after the Delete button:

```svelte
{#if canPurge}
    <button
        onclick={handlePurge}
        disabled={loading !== null}
        class="{btnBase} bg-orange-100 text-orange-700 hover:bg-orange-200 dark:bg-orange-900/30 dark:text-orange-400 dark:hover:bg-orange-900/50"
    >
        {loading === 'purge' ? 'Purging...' : 'Purge'}
    </button>
{/if}
```

- [ ] **Step 3: Build check**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/components/JobRow.svelte frontend/src/lib/components/JobActions.svelte
git commit -m "feat: add checkbox to JobRow, purge action to JobActions"
```

---

### Task 6: Jobs Page Redesign — Stats Bar, Pill Filters, Sortable Headers

**Files:**
- Modify: `frontend/src/routes/jobs/+page.svelte` (full rewrite)

This is the main UI task. The page gets completely rewritten with:
- Stats bar
- Pill-based filters (status, video type, disc type)
- Time range dropdown
- Sortable column headers
- Row checkboxes with select-all
- Gear menu for bulk operations

- [ ] **Step 1: Rewrite the jobs page**

Replace the entire content of `frontend/src/routes/jobs/+page.svelte` with the new implementation. The file is large so the implementer should:

1. Read the current file for reference
2. Read the mockup design description from the spec
3. Build the new page with these sections:

**Script section** state variables needed:
```typescript
import { onMount } from 'svelte';
import { fetchJobs, fetchJobStats, bulkDeleteJobs, bulkPurgeJobs } from '$lib/api/jobs';
import type { Job, JobListResponse } from '$lib/types/arm';
import type { JobStats } from '$lib/api/jobs';
import JobRow from '$lib/components/JobRow.svelte';

let data = $state<JobListResponse | null>(null);
let stats = $state<JobStats | null>(null);
let error = $state<string | null>(null);
let loading = $state(true);

// Pagination
let page = $state(1);
let perPage = $state(25);

// Filters
let statusFilter = $state('');
let videoTypeFilter = $state('');
let disctypeFilter = $state('');
let daysFilter = $state<number | undefined>(undefined);
let searchQuery = $state('');
let searchTimeout: ReturnType<typeof setTimeout>;

// Sorting
let sortBy = $state('start_time');
let sortDir = $state<'asc' | 'desc'>('desc');

// Selection
let selectedJobs = $state<Set<number>>(new Set());

// Gear menu
let gearOpen = $state(false);
let bulkBusy = $state(false);
let bulkFeedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);
```

**Key functions:**
- `load()` — fetches jobs and stats in parallel using current filter/sort/page state
- `loadStats()` — fetches stats with current filters
- `setStatusFilter(val)` — sets status, resets page, reloads
- `setVideoTypeFilter(val)` — sets video type, resets page, reloads
- `setDisctypeFilter(val)` — sets disc type, resets page, reloads
- `setDays(val)` — sets time range, resets page, reloads
- `toggleSort(col)` — if already sorting by col, flip direction; else set col with desc default
- `toggleSelect(jobId, selected)` — add/remove from selectedJobs set
- `toggleSelectAll()` — select/deselect all visible jobs
- `handleBulkDelete(params)` — calls bulkDeleteJobs with confirmation
- `handleBulkPurge(params)` — calls bulkPurgeJobs with confirmation

**Template structure:**

```
<h1>Jobs</h1>

<!-- Stats bar: 5 clickable cards -->
{#if stats}
  <div class="flex gap-3">
    <!-- Total card (primary color) -->
    <!-- Active card (blue) -->
    <!-- Success card (green) -->
    <!-- Failed card (red) -->
    <!-- Waiting card (amber) -->
  </div>
{/if}

<!-- Filter row 1: Search | Status pills | Type pills -->
<div class="flex gap-2 items-center flex-wrap">
  <input search />
  <div> | </div>
  <div>Status: {#each statusOptions} pill {/each}</div>
  <div> | </div>
  <div>Type: {#each typeOptions} pill {/each}</div>
</div>

<!-- Filter row 2: Disc pills | Time range | spacer | selection count | gear -->
<div class="flex gap-2 items-center flex-wrap">
  <div>Disc: {#each discOptions} pill {/each}</div>
  <div> | </div>
  <select>time range</select>
  <div class="flex-1"></div>
  {#if selectedJobs.size > 0}
    <span>{selectedJobs.size} selected</span>
  {/if}
  <!-- Gear dropdown button -->
</div>

<!-- Table with checkbox column + sortable headers -->
<table>
  <thead>
    <th><input checkbox select-all /></th>
    <th onclick sort>Title {sortIndicator}</th>
    <th onclick sort>Year {sortIndicator}</th>
    ...
  </thead>
  <tbody>
    {#each data.jobs as job}
      <JobRow {job} selected={selectedJobs.has(job.job_id)} onselect={toggleSelect} onaction={load} />
    {/each}
  </tbody>
</table>

<!-- Pagination (existing, preserved) -->
```

**Pill button styling:**
- Active: `bg-primary/20 text-primary-text outline outline-2 outline-primary/40 dark:bg-primary/25 dark:text-primary-text-dark`
- Inactive: `bg-primary/5 text-gray-500 hover:bg-primary/10 dark:bg-primary/10 dark:text-gray-400`
- Common: `px-2.5 py-1 rounded-md text-xs font-semibold cursor-pointer`

**Sort indicator function:**
```typescript
function sortIndicator(col: string): string {
    if (sortBy !== col) return '↕';
    return sortDir === 'desc' ? '▼' : '▲';
}
```

**Gear menu dropdown:**
```svelte
<div class="relative">
    <button onclick={() => gearOpen = !gearOpen} class="...">⚙ Actions ▾</button>
    {#if gearOpen}
        <div class="absolute right-0 top-full mt-1 w-60 rounded-lg border ... shadow-lg z-20">
            <!-- Selected section (if selectedJobs.size > 0) -->
            <!-- Bulk actions section -->
        </div>
    {/if}
</div>
```

Close gear menu when clicking outside — use `onclick` on the `<svelte:window>` or a simple blur handler.

- [ ] **Step 2: Build check**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes/jobs/+page.svelte
git commit -m "feat: redesign jobs page with stats bar, pill filters, sortable headers, gear menu"
```

---

### Task 7: Frontend Tests & Full Verification

**Files:**
- Test: `frontend/src/routes/jobs/__tests__/jobs-page.test.ts`

- [ ] **Step 1: Write page tests**

```typescript
// frontend/src/routes/jobs/__tests__/jobs-page.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderComponent, screen, waitFor, fireEvent, cleanup } from '$lib/test-utils';
import JobsPage from '../+page.svelte';

vi.mock('$lib/api/jobs', () => ({
	fetchJobs: vi.fn(() => Promise.resolve({
		jobs: [
			{ job_id: 1, title: 'Test Movie', status: 'success', video_type: 'movie', disctype: 'bluray', year: '2024', start_time: '2026-03-22T12:00:00Z' },
			{ job_id: 2, title: 'Failed Rip', status: 'fail', video_type: 'movie', disctype: 'dvd', year: '2023', start_time: '2026-03-21T12:00:00Z' },
		],
		total: 2, page: 1, per_page: 25, pages: 1,
	})),
	fetchJobStats: vi.fn(() => Promise.resolve({
		total: 2, active: 0, success: 1, fail: 1, waiting: 0,
	})),
	bulkDeleteJobs: vi.fn(() => Promise.resolve({ deleted: 1, errors: [] })),
	bulkPurgeJobs: vi.fn(() => Promise.resolve({ purged: 1, errors: [] })),
	abandonJob: vi.fn(),
	deleteJob: vi.fn(),
	fixJobPermissions: vi.fn(),
}));

describe('Jobs Page', () => {
	beforeEach(() => {
		cleanup();
		vi.clearAllMocks();
	});

	it('renders page title and stats bar', async () => {
		renderComponent(JobsPage);
		await waitFor(() => {
			expect(screen.getByText('Jobs')).toBeInTheDocument();
		});
	});

	it('renders filter pills', async () => {
		renderComponent(JobsPage);
		await waitFor(() => {
			expect(screen.getByText('All')).toBeInTheDocument();
			expect(screen.getByText('Active')).toBeInTheDocument();
			expect(screen.getByText('Success')).toBeInTheDocument();
			expect(screen.getByText('Failed')).toBeInTheDocument();
		});
	});

	it('renders sortable column headers', async () => {
		renderComponent(JobsPage);
		await waitFor(() => {
			expect(screen.getByText(/Title/)).toBeInTheDocument();
			expect(screen.getByText(/Started/)).toBeInTheDocument();
		});
	});

	it('renders gear menu button', async () => {
		renderComponent(JobsPage);
		await waitFor(() => {
			expect(screen.getByText(/Actions/)).toBeInTheDocument();
		});
	});
});
```

- [ ] **Step 2: Run page tests**

Run: `cd frontend && npx vitest run src/routes/jobs/__tests__/jobs-page.test.ts`
Expected: All PASS

- [ ] **Step 3: Run full frontend test suite**

Run: `cd frontend && npx vitest run`
Expected: All PASS

- [ ] **Step 4: Build check**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 5: Run backend tests**

Run: `cd ~/src/automatic-ripping-machine-ui && python3 -m pytest tests/ -x -q`
Expected: All PASS

- [ ] **Step 6: Rebuild and verify live**

```bash
cd ~/src/automatic-ripping-machine-ui/frontend && npm run build
docker restart arm-ui
```

Verify: open http://localhost:8888/jobs — stats bar, pill filters, sortable headers, gear menu should all be functional.

- [ ] **Step 7: Commit tests**

```bash
git add frontend/src/routes/jobs/__tests__/jobs-page.test.ts
git commit -m "test: add jobs page redesign tests"
```
