# Pause/Timer Fix - Design Spec

## Overview

Fix the pause/timer system for waiting jobs so pause state persists across page refreshes, timers hide when paused, and global pause correctly affects all jobs. Remove dead client-side pause state that was never persisted.

## Current Problems

1. **Pause doesn't persist** - CountdownTimer uses client-side `localPaused` state. On page refresh, the timer restarts even though `manual_pause=true` in the DB.
2. **Timer still shows countdown when paused** - Only shows "Paused" text when the timer is BOTH paused AND expired. While paused with time remaining, it displays the frozen countdown.
3. **Resume doesn't reset the timer** - `wait_start_time` is never updated, so after un-pausing the countdown has less time than expected (time passed while paused).
4. **Global pause doesn't hide timers** - Toggling global pause leaves countdown digits visible.
5. **Dead client-side state** - `localPaused`, `localResumed`, `frozenAt`, `offset` in CountdownTimer attempt to track pause duration client-side but are lost on refresh.

## Design

### Pause State Model

A waiting job's effective pause state:

```
effectivePaused = job.manual_pause || globalPaused
```

- `manual_pause` (boolean) - per-job, stored in ARM DB on the Job row
- `globalPaused` (boolean) - `!ripping_enabled` from AppState table, read via dashboard API

**Global pause ON:** All waiting jobs show "Paused". User can still manually start individual jobs via the Start button (existing `startWaitingJob` API, which begins ripping).

**Global pause OFF:** Jobs use their per-job `manual_pause` flag.

**Per-job pause button:** Always visible regardless of global state.

### Timer Display Rules

| State | Display |
|-------|---------|
| `effectivePaused` = true | Pause/play button + "Paused" text. No countdown, no progress bar. |
| `effectivePaused` = false, time remaining | Pause button + "Xm YYs" countdown + progress bar |
| `effectivePaused` = false, expired | "Auto-proceeding..." text |

### DB Persistence

**On pause (per-job button click):**
- UI calls `pauseWaitingJob(jobId)` (existing API)
- ARM sets `manual_pause=true` on the job (existing behavior)

**On resume (per-job button click when paused):**
- UI calls `pauseWaitingJob(jobId)` (same toggle endpoint)
- ARM sets `manual_pause=false` on the job (existing behavior)
- ARM also sets `wait_start_time=now()` so countdown restarts from zero (**new behavior - ARM-neu change**)

**On global pause toggle:**
- UI calls `setRippingEnabled(enabled)` (existing API)
- ARM sets `ripping_paused` on AppState (existing behavior)
- UI re-fetches dashboard, all timers immediately reflect new state
- No per-job DB writes needed

**On page refresh:**
- Dashboard API returns `ripping_enabled` (global state)
- Each job's `manual_pause` field is in the job data
- CountdownTimer receives computed `paused` prop from parent
- Timer renders correctly from DB state - no client-side reconstruction needed

### Component Changes

**CountdownTimer.svelte - Simplify:**

Remove:
- `localPaused` state
- `localResumed` state
- `frozenAt` state
- `offset` state
- `effectivePaused` derived (replaced by `paused` prop being the sole truth)
- `togglePause()` function (parent handles this via `onpause`/`onresume`)

Keep:
- `paused` prop (boolean - computed by parent, single source of truth)
- `startTime`, `waitSeconds`, `inverted` props
- `onpause`, `onresume` callbacks
- `now` state with interval ticker
- `deadline`, `remaining`, `minutes`, `seconds`, `progress`, `expired` derived values

Behavior:
- When `paused`: show play button + "Paused" text, hide countdown and progress bar, stop ticking `now`
- When not paused: show pause button + countdown + progress bar (existing)
- When expired and not paused: show "Auto-proceeding..." (existing)
- Button click calls `onpause()` or `onresume()` based on `paused` prop

**DiscReviewWidget.svelte - Compute effective pause:**

- Add: `let effectivePaused = $derived(paused || !!job.manual_pause)`
- Pass: `paused={effectivePaused}` to CountdownTimer
- `onpause` callback: calls `pauseWaitingJob(job.job_id)` then refreshes (existing)
- `onresume` callback: calls `pauseWaitingJob(job.job_id)` then refreshes (toggle - same endpoint)

**Home page (+page.svelte):**

No changes. Already passes `paused={!dash.ripping_enabled}` to DiscReviewWidget.

### ARM-neu Change (Separate PR)

In `pause_waiting_job` endpoint (`arm/api/v1/jobs.py`):

When setting `manual_pause=false` (resuming), also set `wait_start_time=datetime.now()` so the countdown restarts fresh.

```python
new_val = not (getattr(job, 'manual_pause', False) or False)
updates = {"manual_pause": new_val}
if not new_val:
    # Resuming - reset wait_start_time so countdown restarts from now
    updates["wait_start_time"] = datetime.now()
svc_files.database_updater(updates, job)
```

## Scope

- **UI repo:** CountdownTimer.svelte, DiscReviewWidget.svelte
- **ARM-neu repo:** `arm/api/v1/jobs.py` (pause endpoint - reset wait_start_time on resume)
- No backend (UI FastAPI) changes needed
- No new API endpoints needed
