# Pause/Timer Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix pause/timer persistence so pause state survives page refresh, timers hide when paused, and global pause correctly affects all waiting jobs.

**Architecture:** Remove client-side pause state from CountdownTimer (localPaused, localResumed, frozenAt, offset). Make `paused` prop the single source of truth, computed by parent from `job.manual_pause || globalPaused`. ARM-neu pause endpoint resets `wait_start_time` on resume so countdown restarts fresh.

**Tech Stack:** Svelte 5, ARM-neu Python/FastAPI

**Spec:** `docs/superpowers/specs/2026-04-08-pause-timer-fix-design.md`

---

### Task 1: Create feature branch

- [ ] **Step 1: Create branch**

```bash
cd /home/upb/src/automatic-ripping-machine-ui
git checkout main && git pull
git checkout -b fix/pause-timer-persistence
```

---

### Task 2: Simplify CountdownTimer component

**Files:**
- Modify: `frontend/src/lib/components/CountdownTimer.svelte`
- Modify: `frontend/src/lib/components/CountdownTimer.test.ts`

Remove all client-side pause state. The `paused` prop becomes the sole truth.

- [ ] **Step 1: Update the test for paused-with-time-remaining**

The existing test at line 31 only checks paused+expired. Add a test for paused with time remaining (the main bug - this currently shows the countdown instead of "Paused").

In `frontend/src/lib/components/CountdownTimer.test.ts`, add after the "displays Paused when paused and expired" test (line 36):

```typescript
		it('displays Paused when paused with time remaining', () => {
			renderComponent(CountdownTimer, {
				props: { startTime: '2025-06-15T12:00:00Z', waitSeconds: 120, paused: true }
			});
			expect(screen.getByText('Paused')).toBeInTheDocument();
			expect(screen.queryByText(/\d+m \d+s/)).not.toBeInTheDocument();
		});

		it('hides progress bar when paused', () => {
			const { container } = renderComponent(CountdownTimer, {
				props: { startTime: '2025-06-15T12:00:00Z', waitSeconds: 120, paused: true }
			});
			const progressBar = container.querySelector('[data-progress-fill]');
			expect(progressBar).not.toBeInTheDocument();
		});
```

- [ ] **Step 2: Run tests to verify the new tests fail**

Run: `cd frontend && npx vitest run src/lib/components/CountdownTimer.test.ts`
Expected: The "displays Paused when paused with time remaining" test FAILS (currently shows "2m 00s" not "Paused")

- [ ] **Step 3: Rewrite CountdownTimer.svelte**

Replace the entire content of `frontend/src/lib/components/CountdownTimer.svelte` with:

```svelte
<script lang="ts">
	import { onMount } from 'svelte';

	interface Props {
		startTime: string;
		waitSeconds: number;
		paused?: boolean;
		/** Render with white text/track for use on colored backgrounds */
		inverted?: boolean;
		onpause?: () => void;
		onresume?: () => void;
	}

	let { startTime, waitSeconds, paused = false, inverted = false, onpause, onresume }: Props = $props();

	let now = $state(Date.now());
	let deadline = $derived(new Date(startTime).getTime() + waitSeconds * 1000);
	let remaining = $derived(Math.max(0, Math.ceil((deadline - now) / 1000)));
	let minutes = $derived(Math.floor(remaining / 60));
	let seconds = $derived(remaining % 60);
	let progress = $derived(
		waitSeconds > 0 ? Math.min(1, Math.max(0, 1 - remaining / waitSeconds)) : 1
	);
	let expired = $derived(remaining <= 0);

	function handleClick() {
		if (paused) {
			onresume?.();
		} else {
			onpause?.();
		}
	}

	onMount(() => {
		const id = setInterval(() => {
			if (!paused) {
				now = Date.now();
			}
		}, 1000);
		return () => clearInterval(id);
	});
</script>

<div class="flex items-center gap-2">
	<button
		type="button"
		onclick={handleClick}
		class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full transition-colors
			{inverted
			? 'text-on-primary/90 hover:bg-white/20'
			: 'text-primary-text hover:bg-primary/15 dark:text-primary-text-dark dark:hover:bg-primary/20'}"
		title={paused ? 'Resume timer' : 'Pause timer'}
	>
		{#if paused}
			<!-- Play icon -->
			<svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor">
				<path d="M8 5v14l11-7z" />
			</svg>
		{:else}
			<!-- Pause icon -->
			<svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor">
				<path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
			</svg>
		{/if}
	</button>

	{#if paused}
		<span class="text-sm font-medium {inverted ? 'text-on-primary/90' : 'text-primary-text dark:text-primary-text-dark'}">Paused</span>
	{:else if expired}
		<span class="text-sm font-medium {inverted ? 'text-on-primary/90' : 'text-primary-text dark:text-primary-text-dark'}">Auto-proceeding...</span>
	{:else}
		<span class="text-sm font-medium tabular-nums {inverted ? 'text-on-primary' : 'text-primary-text dark:text-primary-text-dark'}">
			{minutes}m {String(seconds).padStart(2, '0')}s
		</span>
		<div class="h-1.5 w-20 overflow-hidden rounded-full {inverted ? 'bg-on-primary/25' : 'bg-primary/15 dark:bg-primary/15'}">
			<div
				data-progress-fill
				class="h-full rounded-full transition-all duration-1000 {inverted ? 'bg-on-primary/80' : 'bg-primary dark:bg-primary-border'}"
				style="width: {progress * 100}%"
			></div>
		</div>
	{/if}
</div>
```

Key changes:
- Removed: `localPaused`, `localResumed`, `frozenAt`, `offset`, `effectivePaused`, `togglePause()`
- `paused` prop is the sole truth
- `handleClick()` calls `onpause`/`onresume` based on `paused` prop
- When `paused`: only shows "Paused" text (no countdown, no progress bar)
- Progress bar moved inside the `{:else}` block (only shown when not paused and not expired)
- Added `data-progress-fill` attribute for test querying

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/lib/components/CountdownTimer.test.ts`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/components/CountdownTimer.svelte frontend/src/lib/components/CountdownTimer.test.ts
git commit -m "fix: simplify CountdownTimer to use paused prop as sole truth

Remove client-side pause state (localPaused, localResumed, frozenAt,
offset) that was lost on page refresh. The paused prop from the parent
is now the single source of truth. When paused, show only 'Paused'
text - hide countdown and progress bar.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Wire manual_pause into DiscReviewWidget

**Files:**
- Modify: `frontend/src/lib/components/DiscReviewWidget.svelte` (lines 396-410)

Compute effective pause from both global flag and per-job `manual_pause`. Simplify the resume callback.

- [ ] **Step 1: Add effectivePaused derived**

After line 27 (`let { job, driveNames = {}, paused = false, onrefresh, ondismiss }: Props = $props();`), add:

```typescript
let effectivePaused = $derived(paused || !!job.manual_pause);
```

- [ ] **Step 2: Update CountdownTimer usage**

Replace lines 396-411 (the CountdownTimer block in the status bar):

```svelte
		{#if job.source_type !== 'folder' && (job.wait_start_time || job.start_time)}
			<CountdownTimer
				startTime={job.wait_start_time ?? job.start_time ?? ''}
				waitSeconds={waitTime}
				paused={effectivePaused}
				inverted
				onpause={() => { pauseWaitingJob(job.job_id).then(() => onrefresh?.()); }}
				onresume={() => { pauseWaitingJob(job.job_id).then(() => onrefresh?.()); }}
			/>
		{/if}
```

Changes:
- `paused={effectivePaused}` instead of `{paused}` (now includes `manual_pause`)
- `onresume` simplified: always calls `pauseWaitingJob` (toggle endpoint) then refreshes. The old code had a confusing branch where globally-paused resume called `startWaitingJob` (which starts ripping, not resume timer). Resume should just un-pause the timer, not start the rip.

- [ ] **Step 3: Run full test suite**

Run: `cd frontend && npx vitest run`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/components/DiscReviewWidget.svelte
git commit -m "fix: wire manual_pause into DiscReviewWidget pause state

Compute effectivePaused from global ripping_enabled AND per-job
manual_pause. Simplify resume callback to always toggle pause
(not start ripping). Timer now reflects DB pause state on refresh.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: ARM-neu - reset wait_start_time on resume

**Files:**
- Modify: `/home/upb/src/automatic-ripping-machine-neu/arm/api/v1/jobs.py` (pause_waiting_job function)

When the pause endpoint toggles `manual_pause` to `false` (resuming), also reset `wait_start_time` so the countdown restarts from zero.

- [ ] **Step 1: Switch to ARM-neu repo and create branch**

```bash
cd /home/upb/src/automatic-ripping-machine-neu
git checkout main && git pull
git checkout -b fix/pause-reset-wait-time
```

- [ ] **Step 2: Find and update pause_waiting_job**

Find the function with: `grep -n 'def pause_waiting' arm/api/v1/jobs.py`

Update the function. The current code is:

```python
new_val = not (getattr(job, 'manual_pause', False) or False)
svc_files.database_updater({"manual_pause": new_val}, job)
return {"success": True, "job_id": job.job_id, "paused": new_val}
```

Replace with:

```python
new_val = not (getattr(job, 'manual_pause', False) or False)
updates = {"manual_pause": new_val}
if not new_val:
    # Resuming - reset wait_start_time so the UI countdown restarts from now
    from datetime import datetime
    updates["wait_start_time"] = datetime.now()
svc_files.database_updater(updates, job)
return {"success": True, "job_id": job.job_id, "paused": new_val}
```

- [ ] **Step 3: Run ARM tests**

Run: `cd /home/upb/src/automatic-ripping-machine-neu && python3 -m pytest test/ -v --tb=short -k pause 2>&1 | tail -20`
Expected: Tests pass (or no pause-specific tests exist)

- [ ] **Step 4: Commit (no Co-Authored-By per CLAUDE.md)**

```bash
git add arm/api/v1/jobs.py
git commit -m "fix: reset wait_start_time when resuming a paused job

When pause_waiting_job toggles manual_pause to false (resuming),
also set wait_start_time to now() so the UI countdown timer
restarts from zero instead of showing stale remaining time."
```

- [ ] **Step 5: Push and create PR**

```bash
git push -u origin fix/pause-reset-wait-time
gh pr create -R uprightbass360/automatic-ripping-machine-neu \
  --title "fix: reset wait_start_time when resuming a paused job" \
  --body "When un-pausing a waiting job, reset wait_start_time to now() so the UI countdown restarts fresh instead of continuing from the stale pre-pause timestamp."
```

---

### Task 5: Deploy and verify

**Files:** None (deployment only)

- [ ] **Step 1: Deploy ARM-neu fix to hifi-server**

```bash
ssh hifi-server "git -C /home/upb/src/automatic-ripping-machine-neu fetch origin && git -C /home/upb/src/automatic-ripping-machine-neu checkout fix/pause-reset-wait-time"
ssh hifi-server "docker compose -f /home/upb/src/automatic-ripping-machine-neu/docker-compose.yml -f /home/upb/src/automatic-ripping-machine-neu/docker-compose.dev.yml up -d --build arm-rippers"
```

- [ ] **Step 2: Build and deploy UI fix**

```bash
cd /home/upb/src/automatic-ripping-machine-ui/frontend && npm run build
rsync -avz --delete frontend/build/ hifi-server:/home/upb/src/automatic-ripping-machine-ui/frontend/build/
ssh hifi-server "docker compose -f /home/upb/src/automatic-ripping-machine-neu/docker-compose.yml -f /home/upb/src/automatic-ripping-machine-neu/docker-compose.dev.yml restart arm-ui"
```

- [ ] **Step 3: Push UI branch and create PR**

```bash
cd /home/upb/src/automatic-ripping-machine-ui
git push -u origin fix/pause-timer-persistence
gh pr create -R uprightbass360/automatic-ripping-machine-ui \
  --title "fix: persist pause state across refresh, hide timer when paused" \
  --body "## Summary
- Simplify CountdownTimer: remove client-side pause state, use paused prop as sole truth
- Wire job.manual_pause into DiscReviewWidget so pause survives page refresh
- When paused, show only 'Paused' text (hide countdown and progress bar)
- Global pause correctly hides all timers

## Test plan
- [ ] Pause a waiting job, refresh page - timer should show 'Paused'
- [ ] Resume a paused job - countdown restarts from zero
- [ ] Toggle global pause - all waiting job timers show 'Paused'
- [ ] Toggle global pause off - timers resume from their wait_start_time"
```

- [ ] **Step 4: Verify on hifi-server**

Test with a waiting job:
1. Pause the timer - shows "Paused", no countdown
2. Refresh the page - still shows "Paused" (persisted via manual_pause)
3. Resume the timer - countdown restarts from zero (fresh wait_start_time)
4. Toggle global pause on - all timers show "Paused"
5. Toggle global pause off - timers resume
