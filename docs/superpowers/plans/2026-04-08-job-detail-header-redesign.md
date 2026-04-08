# Job Detail Header Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize the job detail page header into a single structured container with title bar, poster, bordered metadata grid, panel toggle bar, and expanded panel content.

**Architecture:** Replace the current loose layout (poster + title line + action bar + flat dl grid + separate toggle buttons) with one unified container. The container has 4 sections: title bar (title/badges/actions), poster+grid body, panel toggle bar, and expandable panel content. The metadata grid uses 4 columns with full cell borders, auto-padding empty cells.

**Tech Stack:** Svelte 5, Tailwind CSS 4, existing component library (StatusBadge, JobActions, TitleSearch, etc.)

**Spec:** `docs/superpowers/specs/2026-04-08-job-detail-header-redesign.md`

---

### Task 1: Create feature branch

**Files:**
- None (git only)

- [ ] **Step 1: Create and switch to feature branch**

```bash
git checkout main
git pull
git checkout -b feat/job-detail-header-redesign
```

- [ ] **Step 2: Verify branch**

```bash
git branch --show-current
```
Expected: `feat/job-detail-header-redesign`

---

### Task 2: Build the metadata field list helper

**Files:**
- Create: `frontend/src/lib/utils/job-fields.ts`
- Test: `frontend/src/lib/__tests__/job-fields.test.ts`

This helper computes the ordered list of metadata fields to display for any given job, based on type and state. Each field is a `{ label: string; value: string; mono?: boolean; link?: string; isSelect?: boolean }` object.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/lib/__tests__/job-fields.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { buildMetadataFields } from '$lib/utils/job-fields';
import type { JobDetail } from '$lib/types/arm';

function makeJob(overrides: Partial<JobDetail> = {}): JobDetail {
	return {
		job_id: 1, title: 'The Matrix', year: '1999', status: 'success',
		video_type: 'movie', disctype: 'bluray', label: 'THE_MATRIX',
		devpath: '/dev/sr0', source_type: 'disc', no_of_titles: 24,
		start_time: '2026-04-07T22:26:00Z', stop_time: '2026-04-08T00:06:00Z',
		job_length: '1:40:12', multi_title: false, crc_id: null, imdb_id: 'tt0133093',
		path: '/home/arm/media/movies/The Matrix (1999)', raw_path: null,
		transcode_path: null, disc_number: null, disc_total: null,
		season: null, season_auto: null, tvdb_id: null,
		artist: null, artist_auto: null, album: null, album_auto: null,
		source_path: null, tracks: [], config: {},
		arm_version: null, logfile: null, stage: null, errors: null,
		mountpoint: null, hasnicetitle: null, poster_url: null,
		poster_url_auto: null, poster_url_manual: null,
		title_auto: null, title_manual: null, year_auto: null, year_manual: null,
		video_type_auto: null, video_type_manual: null,
		imdb_id_auto: null, imdb_id_manual: null,
		artist_manual: null, album_manual: null,
		season_manual: null, episode: null, episode_auto: null, episode_manual: null,
		transcode_overrides: null, title_pattern_override: null, folder_pattern_override: null,
		ejected: null, pid: null, manual_pause: null, wait_start_time: null,
		tracks_total: null, tracks_ripped: null,
	} as unknown as JobDetail;
}

describe('buildMetadataFields', () => {
	it('returns correct fields for a completed movie', () => {
		const fields = buildMetadataFields(makeJob());
		const labels = fields.map(f => f.label);
		expect(labels).toContain('Type');
		expect(labels).toContain('Disc Type');
		expect(labels).toContain('Title Mode');
		expect(labels).toContain('Titles');
		expect(labels).toContain('Label');
		expect(labels).toContain('Device');
		expect(labels).toContain('Source');
		expect(labels).toContain('IMDb');
		expect(labels).toContain('Started');
		expect(labels).toContain('Finished');
		expect(labels).toContain('Duration');
		expect(labels).toContain('Output');
		expect(labels).not.toContain('CRC');
		expect(labels).not.toContain('Season');
		expect(labels).not.toContain('Artist');
	});

	it('includes CRC only for DVD with crc_id', () => {
		const fields = buildMetadataFields(makeJob({ disctype: 'dvd', crc_id: 'abc123' }));
		const labels = fields.map(f => f.label);
		expect(labels).toContain('CRC');
	});

	it('excludes CRC for bluray even with crc_id', () => {
		const fields = buildMetadataFields(makeJob({ crc_id: 'abc123' }));
		const labels = fields.map(f => f.label);
		expect(labels).not.toContain('CRC');
	});

	it('includes Season and TVDB for series', () => {
		const fields = buildMetadataFields(makeJob({ video_type: 'series', season: '1', tvdb_id: 81189 }));
		const labels = fields.map(f => f.label);
		expect(labels).toContain('Season');
		expect(labels).toContain('TVDB');
	});

	it('includes Artist and Album for music, excludes Title Mode', () => {
		const fields = buildMetadataFields(makeJob({
			disctype: 'music', video_type: 'music',
			artist: 'The Beatles', album: 'Abbey Road',
		}));
		const labels = fields.map(f => f.label);
		expect(labels).toContain('Artist');
		expect(labels).toContain('Album');
		expect(labels).not.toContain('Title Mode');
		expect(labels).not.toContain('IMDb');
	});

	it('shows Elapsed instead of Finished/Duration for active jobs', () => {
		const fields = buildMetadataFields(makeJob({ status: 'ripping', stop_time: null, job_length: null }));
		const labels = fields.map(f => f.label);
		expect(labels).toContain('Elapsed');
		expect(labels).not.toContain('Finished');
		expect(labels).not.toContain('Duration');
	});

	it('includes disc number when present', () => {
		const fields = buildMetadataFields(makeJob({ disc_number: 2, disc_total: 4 }));
		const labels = fields.map(f => f.label);
		expect(labels).toContain('Disc #');
		const discField = fields.find(f => f.label === 'Disc #');
		expect(discField?.value).toBe('2 of 4');
	});

	it('includes source path for folder imports', () => {
		const fields = buildMetadataFields(makeJob({ source_type: 'folder', source_path: '/mnt/ingress/movies' }));
		const labels = fields.map(f => f.label);
		expect(labels).toContain('Source Path');
	});

	it('marks mono fields correctly', () => {
		const fields = buildMetadataFields(makeJob());
		const labelField = fields.find(f => f.label === 'Label');
		expect(labelField?.mono).toBe(true);
	});

	it('marks IMDb as linked', () => {
		const fields = buildMetadataFields(makeJob());
		const imdbField = fields.find(f => f.label === 'IMDb');
		expect(imdbField?.link).toContain('imdb.com');
	});

	it('pads fields to multiple of 4', () => {
		const fields = buildMetadataFields(makeJob());
		expect(fields.length % 4).toBe(0);
	});
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/lib/__tests__/job-fields.test.ts`
Expected: FAIL - module not found

- [ ] **Step 3: Write the implementation**

Create `frontend/src/lib/utils/job-fields.ts`:

```typescript
import type { JobDetail } from '$lib/types/arm';
import { formatDateTime, timeAgo } from '$lib/utils/format';
import { discTypeLabel, isJobActive } from '$lib/utils/job-type';

export interface MetadataField {
	label: string;
	value: string;
	mono?: boolean;
	link?: string;
	/** When true, this cell renders the Title Mode <select> instead of a text value */
	isSelect?: boolean;
	/** Empty placeholder cell for grid padding */
	empty?: boolean;
}

export function buildMetadataFields(job: JobDetail): MetadataField[] {
	const fields: MetadataField[] = [];
	const active = isJobActive(job.status);
	const isMusic = job.disctype === 'music' || job.video_type === 'music';
	const isVideo = job.disctype === 'dvd' || job.disctype === 'bluray' || job.disctype === 'bluray4k';

	// Type
	if (!isMusic) {
		fields.push({ label: 'Type', value: job.video_type ?? 'N/A' });
	} else {
		fields.push({ label: 'Type', value: 'Music' });
	}

	// Disc Type
	fields.push({ label: 'Disc Type', value: discTypeLabel(job.disctype) });

	// Title Mode (video only)
	if (isVideo) {
		fields.push({ label: 'Title Mode', value: job.multi_title ? 'multi' : 'single', isSelect: true });
	}

	// Titles
	fields.push({ label: 'Titles', value: String(job.no_of_titles ?? 'N/A') });

	// Season (series only)
	const season = job.season || job.season_auto;
	if (season && !isMusic) {
		fields.push({ label: 'Season', value: String(season) });
	}

	// Disc # (multi-disc)
	if (job.disc_number) {
		const val = job.disc_total ? `${job.disc_number} of ${job.disc_total}` : String(job.disc_number);
		fields.push({ label: 'Disc #', value: val });
	}

	// Artist / Album (music)
	const artist = job.artist || job.artist_auto;
	if (artist && isMusic) {
		fields.push({ label: 'Artist', value: artist });
	}
	const album = job.album || job.album_auto;
	if (album && isMusic) {
		fields.push({ label: 'Album', value: album });
	}

	// Label
	if (job.label) {
		fields.push({ label: 'Label', value: job.label, mono: true });
	}

	// Device
	if (job.devpath) {
		fields.push({ label: 'Device', value: job.devpath });
	}

	// Source
	fields.push({ label: 'Source', value: job.source_type === 'folder' ? 'Folder' : 'Disc' });

	// Source Path (folder imports)
	if (job.source_type === 'folder' && job.source_path) {
		fields.push({ label: 'Source Path', value: job.source_path, mono: true });
	}

	// CRC (DVD only, when present)
	if (job.crc_id && job.disctype === 'dvd') {
		fields.push({ label: 'CRC', value: job.crc_id, mono: true });
	}

	// IMDb (video only, when present)
	if (job.imdb_id && !isMusic) {
		fields.push({ label: 'IMDb', value: job.imdb_id, link: `https://www.imdb.com/title/${job.imdb_id}/` });
	}

	// TVDB (series, when present)
	if (job.tvdb_id && !isMusic) {
		fields.push({ label: 'TVDB', value: String(job.tvdb_id), link: `https://thetvdb.com/?id=${job.tvdb_id}&tab=series` });
	}

	// Timing
	fields.push({ label: 'Started', value: formatDateTime(job.start_time) });

	if (active) {
		fields.push({ label: 'Elapsed', value: job.start_time ? timeAgo(job.start_time) : 'N/A' });
	} else {
		if (job.stop_time) {
			fields.push({ label: 'Finished', value: formatDateTime(job.stop_time) });
		}
		if (job.job_length) {
			fields.push({ label: 'Duration', value: job.job_length });
		}
	}

	// Paths
	if (job.path) {
		fields.push({ label: 'Output', value: job.path, mono: true });
	}
	if (job.raw_path) {
		fields.push({ label: 'Raw', value: job.raw_path, mono: true });
	}
	if (job.transcode_path) {
		fields.push({ label: 'Transcode', value: job.transcode_path, mono: true });
	}

	// Pad to multiple of 4
	while (fields.length % 4 !== 0) {
		fields.push({ label: '', value: '', empty: true });
	}

	return fields;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/lib/__tests__/job-fields.test.ts`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/utils/job-fields.ts frontend/src/lib/__tests__/job-fields.test.ts
git commit -m "feat: add buildMetadataFields helper for job detail header grid

Computes ordered metadata field list based on job type and state.
Handles video/music/series/folder variants, pads to 4-column grid.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Rewrite the header template

**Files:**
- Modify: `frontend/src/routes/jobs/[id]/+page.svelte` (lines 249-497)

This is the main task. Replace everything from the back link through the panel content (but NOT the tracks table or debug section) with the new container structure.

- [ ] **Step 1: Add the import for buildMetadataFields**

At the top of the `<script>` section, add:

```typescript
import { buildMetadataFields } from '$lib/utils/job-fields';
```

And add a derived value after the existing derived values (around line 128):

```typescript
let metadataFields = $derived(job ? buildMetadataFields(job) : []);
```

- [ ] **Step 2: Replace the header section**

Replace from `<!-- Back link -->` (line 252) through the closing `{/if}` of the active panel content (line 497) with the new container structure. Keep the `<!-- Auto vs Manual title info -->` banner and inline log feeds - move them outside and below the container.

The new template (replaces lines 252-497):

```svelte
		<!-- Breadcrumb -->
		<nav class="text-sm">
			<a href="/" class="text-primary-text hover:underline dark:text-primary-text-dark">Dashboard</a>
			<span class="mx-1.5 text-gray-400 dark:text-gray-500">&rsaquo;</span>
			<span class="text-gray-500 dark:text-gray-400">{job.title || job.label || 'Untitled'}</span>
		</nav>

		<!-- Main header container -->
		<div class="rounded-lg border border-primary/20 bg-surface shadow-xs dark:border-primary/20 dark:bg-surface-dark overflow-hidden">

			<!-- Title bar -->
			<div class="flex flex-wrap items-center gap-2 border-b border-primary/15 px-5 py-3 dark:border-primary/15">
				<h1 class="text-xl font-bold text-gray-900 dark:text-white">
					{job.title || job.label || 'Untitled'}
				</h1>
				{#if job.year && job.year !== '0000'}
					<span class="text-base text-gray-400 dark:text-gray-500">({job.year})</span>
				{/if}
				<StatusBadge status={isFolderImport && job.status === 'ripping' ? 'importing' : job.status} />
				{#if job.multi_title}
					<span class="rounded-full bg-purple-100 px-2.5 py-0.5 text-[10px] font-semibold uppercase text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">Multi-Title</span>
				{/if}
				{#if job.imdb_id && !isMusicDisc}
					<a
						href="https://www.imdb.com/title/{job.imdb_id}"
						target="_blank"
						rel="noopener noreferrer"
						class="rounded-full bg-yellow-400 px-2.5 py-0.5 text-[10px] font-bold text-black"
					>IMDb</a>
				{/if}

				<!-- Action buttons pushed right -->
				<div class="flex flex-wrap items-center gap-2 ml-auto">
					{#if isVideoDisc && (job.status === 'success' || job.status === 'fail')}
						<button
							onclick={handleRetranscode}
							disabled={retranscoding}
							class="rounded-full px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50 bg-indigo-100 text-indigo-700 hover:bg-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 dark:hover:bg-indigo-900/50"
						>
							{retranscoding ? 'Queuing...' : 'Re-transcode'}
						</button>
					{/if}
					<JobActions {job} onaction={loadJob} ondelete={() => goto('/')} compact={false} />
					{#if retranscodeFeedback}
						<span class="text-xs {retranscodeFeedback.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
							{retranscodeFeedback.message}
						</span>
					{/if}
				</div>
			</div>

			<!-- Poster + Metadata grid -->
			<div class="flex items-start">
				<!-- Poster -->
				<div class="shrink-0 border-r border-primary/15 p-4 dark:border-primary/15">
					{#if job.poster_url}
						<img
							src={posterSrc(job.poster_url)}
							alt={job.title ?? 'Poster'}
							class="rounded-md object-cover shadow-sm {isMusicDisc ? 'h-[120px] w-[120px]' : 'w-[120px]'}"
							style={isMusicDisc ? '' : 'aspect-ratio: 2/3'}
							onerror={posterFallback}
						/>
					{:else}
						<div
							class="flex items-center justify-center rounded-md border border-dashed border-primary/20 bg-primary/5 dark:border-primary/15 dark:bg-primary/5 {isMusicDisc ? 'h-[120px] w-[120px]' : 'w-[120px]'}"
							style={isMusicDisc ? '' : 'aspect-ratio: 2/3'}
						>
							<svg class="h-8 w-8 text-gray-400 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
								<circle cx="12" cy="12" r="10" />
								<circle cx="12" cy="12" r="3" />
							</svg>
						</div>
					{/if}
				</div>

				<!-- Metadata grid -->
				<div class="flex-1 grid grid-cols-4">
					{#each metadataFields as field, i}
						{@const isLastRow = i >= metadataFields.length - 4}
						{@const isRightEdge = (i + 1) % 4 === 0}
						<div class="px-4 py-3 {!isLastRow ? 'border-b border-primary/15 dark:border-primary/15' : ''} {!isRightEdge ? 'border-r border-primary/15 dark:border-primary/15' : ''}">
							{#if !field.empty}
								<div class="text-[11px] uppercase tracking-wider text-gray-500 dark:text-gray-400">{field.label}</div>
								{#if field.isSelect}
									<div class="mt-1">
										<select
											value={job.multi_title ? 'multi' : 'single'}
											onchange={(e) => { const v = e.currentTarget.value; if ((v === 'multi') !== !!job?.multi_title) handleToggleMultiTitle(); }}
											disabled={togglingMultiTitle}
											class="rounded-md border border-primary/25 bg-primary/5 px-3 py-2 text-sm text-gray-900 focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white"
										>
											<option value="single">Single Title</option>
											<option value="multi">Multi-Title</option>
										</select>
									</div>
								{:else if field.link}
									<a href={field.link} target="_blank" rel="noopener noreferrer" class="mt-1 block text-sm font-medium text-primary hover:underline dark:text-primary {field.mono ? 'font-mono text-xs' : ''}">{field.value}</a>
								{:else}
									<div class="mt-1 text-sm font-medium text-gray-900 dark:text-white {field.mono ? 'font-mono text-xs truncate' : ''}" title={field.mono ? field.value : undefined}>{field.value}</div>
								{/if}
							{/if}
						</div>
					{/each}
				</div>
			</div>

			<!-- Panel toggle bar -->
			<div class="flex border-t border-primary/15 bg-surface/50 dark:border-primary/15 dark:bg-surface-dark/50">
				{#if isVideoDisc}
					<button
						onclick={() => (activePanel = activePanel === 'title' ? null : 'title')}
						class="flex-1 border-r border-primary/15 px-4 py-2.5 text-center text-sm font-medium transition-colors dark:border-primary/15 {activePanel === 'title' ? 'text-primary border-b-2 border-b-primary bg-primary/5 dark:bg-primary/10' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
					>Identify</button>
				{/if}
				{#if isMusicDisc}
					<button
						onclick={() => (activePanel = activePanel === 'music' ? null : 'music')}
						class="flex-1 border-r border-primary/15 px-4 py-2.5 text-center text-sm font-medium transition-colors dark:border-primary/15 {activePanel === 'music' ? 'text-primary border-b-2 border-b-primary bg-primary/5 dark:bg-primary/10' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
					>Search Music</button>
				{/if}
				{#if job.config}
					<button
						onclick={() => (activePanel = activePanel === 'rip' ? null : 'rip')}
						class="flex-1 border-r border-primary/15 px-4 py-2.5 text-center text-sm font-medium transition-colors dark:border-primary/15 {activePanel === 'rip' ? 'text-primary border-b-2 border-b-primary bg-primary/5 dark:bg-primary/10' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
					>Rip Settings</button>
				{/if}
				{#if isVideoDisc && (job.video_type === 'series' || job.imdb_id)}
					<button
						onclick={() => (activePanel = activePanel === 'tvdb' ? null : 'tvdb')}
						class="flex-1 border-r border-primary/15 px-4 py-2.5 text-center text-sm font-medium transition-colors dark:border-primary/15 {activePanel === 'tvdb' ? 'text-primary border-b-2 border-b-primary bg-primary/5 dark:bg-primary/10' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
					>Episodes</button>
				{/if}
				{#if isVideoDisc}
					<button
						onclick={() => (activePanel = activePanel === 'transcode' ? null : 'transcode')}
						class="flex-1 border-r border-primary/15 px-4 py-2.5 text-center text-sm font-medium transition-colors dark:border-primary/15 {activePanel === 'transcode' ? 'text-primary border-b-2 border-b-primary bg-primary/5 dark:bg-primary/10' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
					>Transcode Settings</button>
				{/if}
				{#if hasCrcData}
					<button
						onclick={() => (activePanel = activePanel === 'crc' ? null : 'crc')}
						class="flex-1 px-4 py-2.5 text-center text-sm font-medium transition-colors {activePanel === 'crc' ? 'text-primary border-b-2 border-b-primary bg-primary/5 dark:bg-primary/10' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
					>CRC Lookup</button>
				{/if}
			</div>

			<!-- Active panel content -->
			{#if activePanel === 'title'}
				<div class="border-t border-primary/15 p-5 dark:border-primary/15">
					<TitleSearch {job} onapply={handleTitleApply} />
				</div>
			{:else if activePanel === 'music'}
				<div class="border-t border-primary/15 p-5 dark:border-primary/15">
					<MusicSearch {job} onapply={handleTitleApply} />
				</div>
			{:else if activePanel === 'crc'}
				<div class="border-t border-primary/15 p-5 dark:border-primary/15">
					<CrcLookup {job} onapply={loadJob} />
				</div>
			{:else if activePanel === 'rip'}
				<div class="border-t border-primary/15 p-5 dark:border-primary/15">
					<RipSettings {job} config={job.config!} isMusic={isMusicDisc} multiTitle={!!job.multi_title} onsaved={handleConfigSaved} />
				</div>
			{:else if activePanel === 'tvdb'}
				<div class="border-t border-primary/15 p-5 dark:border-primary/15">
					<EpisodeMatch {job} onapply={loadJob} />
				</div>
			{:else if activePanel === 'transcode'}
				<div class="border-t border-primary/15 p-5 dark:border-primary/15">
					<TranscodeOverrides {job} onsaved={loadJob} />
				</div>
			{/if}
		</div>

		<!-- Auto vs Manual title info (outside container) -->
		{#if hasAutoManualDiff}
			<div class="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm dark:border-amber-800 dark:bg-amber-900/20">
				<svg class="h-4 w-4 shrink-0 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
				<span class="text-amber-800 dark:text-amber-300">
					Auto-detected: <span class="font-medium">{job.title_auto}{#if job.year_auto} ({job.year_auto}){/if}</span>
				</span>
			</div>
		{/if}

		{#if job.errors}
			<div class="rounded-lg border p-3 text-sm {job.status === 'success'
				? 'border-yellow-200 bg-yellow-50 text-yellow-700 dark:border-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
				: 'border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400'}">
				<strong>{job.status === 'success' ? 'Warnings:' : 'Errors:'}</strong> {job.errors}
			</div>
		{/if}

		{#if job.logfile}
			<InlineLogFeed logfile={job.logfile} maxEntries={15} title="ARM Ripper Log" />
		{/if}
		{#if transcoderLogfile && !isMusicDisc && job?.disctype !== 'data' && job?.status !== 'ripping' && job?.status !== 'ready' && job?.status !== 'identifying' && job?.status !== 'waiting'}
			<InlineLogFeed
				logfile={transcoderLogfile}
				maxEntries={15}
				title="Transcoder Log"
				fetchFn={fetchStructuredTranscoderLogContent}
				logLinkBase="/logs/transcoder"
			/>
		{/if}
```

- [ ] **Step 3: Verify the dev server renders correctly**

Run: Visit http://localhost:5174/jobs/1 in the browser
Expected: The Matrix job shows the new container layout with title bar, poster, 4-col grid, and panel toggle bar

- [ ] **Step 4: Check multiple job types render**

Visit:
- http://localhost:5174/jobs/4 (series - Breaking Bad)
- http://localhost:5174/jobs/9 (music - Abbey Road)
- http://localhost:5174/jobs/8 (waiting - Mystery Disc)
- http://localhost:5174/jobs/11 (waiting with IMDb - Dark Knight)

Expected: Each shows appropriate fields, no empty grids, panel bar adapts to job type

- [ ] **Step 5: Commit**

```bash
git add frontend/src/routes/jobs/[id]/+page.svelte
git commit -m "feat: redesign job detail header into structured container

Single container with title bar (badges + actions), poster + 4-col
bordered metadata grid, and panel toggle bar. Fields adapt by job type.
Replaces flat layout with settings-page styling patterns.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Update the JobActions button styling to pill

**Files:**
- Modify: `frontend/src/lib/components/JobActions.svelte` (line 97-101)

The action buttons need to use pill styling (`rounded-full`) to match the title bar context.

- [ ] **Step 1: Update the btnBase derived value**

In `JobActions.svelte`, change the `btnBase` derived value (line 97-101) from:

```typescript
let btnBase = $derived(
	compact
		? 'rounded px-2 py-0.5 text-xs font-medium disabled:opacity-50 transition-colors'
		: 'rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-50 transition-colors'
);
```

to:

```typescript
let btnBase = $derived(
	compact
		? 'rounded px-2 py-0.5 text-xs font-medium disabled:opacity-50 transition-colors'
		: 'rounded-full px-3 py-1.5 text-xs font-medium disabled:opacity-50 transition-colors'
);
```

Changes: `rounded-lg` to `rounded-full`, `text-sm` to `text-xs`.

- [ ] **Step 2: Add outline borders to destructive buttons**

Update the Delete button class (line 128) from:

```svelte
class="{btnBase} bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50"
```

to:

```svelte
class="{btnBase} bg-red-100 text-red-700 ring-1 ring-red-200 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 dark:ring-red-800 dark:hover:bg-red-900/50"
```

Update the Purge button class (line 137) from:

```svelte
class="{btnBase} bg-orange-100 text-orange-700 hover:bg-orange-200 dark:bg-orange-900/30 dark:text-orange-400 dark:hover:bg-orange-900/50"
```

to:

```svelte
class="{btnBase} bg-orange-100 text-orange-700 ring-1 ring-orange-200 hover:bg-orange-200 dark:bg-orange-900/30 dark:text-orange-400 dark:ring-orange-800 dark:hover:bg-orange-900/50"
```

Update the Fix Permissions button class (line 119) from:

```svelte
class="{btnBase} bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:hover:bg-blue-900/50"
```

to:

```svelte
class="{btnBase} bg-blue-100 text-blue-700 ring-1 ring-blue-200 hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:ring-blue-800 dark:hover:bg-blue-900/50"
```

- [ ] **Step 3: Verify buttons render as pills**

Visit: http://localhost:5174/jobs/1
Expected: Action buttons in title bar are pill-shaped with outlined destructive buttons

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/components/JobActions.svelte
git commit -m "fix: update JobActions buttons to pill style with outlined destructive actions

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Update existing tests

**Files:**
- Modify: `frontend/src/routes/jobs/__tests__/job-detail-page.test.ts`

The existing tests check for elements that moved (e.g., status text, disc type). Update them to work with the new layout.

- [ ] **Step 1: Update mock to include fields needed by buildMetadataFields**

In the mock `fetchJob` return value (line 15-25), add missing fields:

```typescript
fetchJob: vi.fn(() => Promise.resolve({
	job_id: 1, title: 'Test Movie', status: 'success', video_type: 'movie',
	year: '2024', disctype: 'bluray', label: 'TEST_MOVIE', start_time: '2025-06-15T10:00:00Z',
	stop_time: '2025-06-15T11:00:00Z', job_length: '1h 0m', devpath: '/dev/sr0',
	imdb_id: 'tt1234567', poster_url: null, errors: null, stage: null,
	no_of_titles: 3, logfile: 'job_1.log', crc_id: 'abc123', multi_title: false,
	source_type: 'disc', source_path: null, path: null, raw_path: null, transcode_path: null,
	disc_number: null, disc_total: null, season: null, season_auto: null, tvdb_id: null,
	artist: null, artist_auto: null, album: null, album_auto: null,
	tracks: [
		{ track_id: 1, job_id: 1, track_number: '1', length: 7200, aspect_ratio: '16:9', fps: 24, enabled: true, basename: 'title_01', filename: 'title_01.mkv', orig_filename: 'title_01.mkv', new_filename: null, ripped: true, status: 'success', error: null, source: null, title: null, year: null, imdb_id: null, poster_url: null, video_type: null, episode_number: null, episode_name: null, custom_filename: null }
	],
	config: {}
})),
```

- [ ] **Step 2: Update the breadcrumb test expectation**

The "Back to Dashboard" link is now a breadcrumb. The existing tests should still pass since they check for title, status badge, and disc type which are still rendered. Add a breadcrumb test:

```typescript
it('renders breadcrumb navigation', async () => {
	renderComponent(JobDetailPage);
	await waitFor(() => {
		expect(screen.getByText('Dashboard')).toBeInTheDocument();
	});
});
```

- [ ] **Step 3: Run all tests**

Run: `cd frontend && npx vitest run`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/jobs/__tests__/job-detail-page.test.ts
git commit -m "test: update job detail page tests for header redesign

Add missing mock fields for buildMetadataFields, add breadcrumb test.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Remove the Log button reference from home page transcoder fix

**Files:**
- Verify: `frontend/src/routes/+page.svelte`

- [ ] **Step 1: Verify the transcoder layout fix from earlier is still in place**

Check that the transcoder section on the home page uses `space-y-2` not the grid layout:

```bash
cd frontend && grep -n "space-y-2" src/routes/+page.svelte | head -5
```

Expected: The active transcodes section should show `space-y-2`

- [ ] **Step 2: Run the full test suite**

Run: `cd frontend && npx vitest run`
Expected: All tests pass

- [ ] **Step 3: Commit any remaining changes**

Only commit if there are uncommitted changes from the transcoder fix:

```bash
git add frontend/src/routes/+page.svelte
git commit -m "fix: use full-width row layout for transcoder cards on home page

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Final verification and cleanup

**Files:**
- None (verification only)

- [ ] **Step 1: Run the full test suite**

Run: `cd frontend && npx vitest run`
Expected: All tests pass, no regressions

- [ ] **Step 2: Visual verification across job types**

Visit each job type in the browser and verify:
- http://localhost:5174/jobs/1 (movie, success) - 4-col grid, poster, all fields
- http://localhost:5174/jobs/4 (series, transcoding) - has Title Mode select
- http://localhost:5174/jobs/9 (music) - no Title Mode, shows Artist/Album if present
- http://localhost:5174/jobs/8 (waiting, unidentified) - minimal fields, empty padded cells
- http://localhost:5174/jobs/11 (waiting, identified) - IMDb badge and field
- http://localhost:5174/jobs/2 (DVD, success) - CRC field and CRC Lookup panel button

- [ ] **Step 3: Verify panel toggles work**

Click each panel button and confirm content expands within the container. Click again to collapse.

- [ ] **Step 4: Push branch**

```bash
git push -u origin feat/job-detail-header-redesign
```
