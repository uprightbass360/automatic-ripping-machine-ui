<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchDashboard } from '$lib/api/dashboard';
	import { fetchJobs, fetchJobProgress, fetchJobStats, bulkDeleteJobs, bulkPurgeJobs } from '$lib/api/jobs';
	import type { RipProgress, JobStats } from '$lib/api/jobs';
	import type { DashboardData, JobListResponse } from '$lib/types/arm';
	import DiscReviewWidget from '$lib/components/DiscReviewWidget.svelte';
	import JobCard from '$lib/components/JobCard.svelte';
	import ActiveJobRow from '$lib/components/ActiveJobRow.svelte';
	import JobRow from '$lib/components/JobRow.svelte';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import TranscodeCard from '$lib/components/TranscodeCard.svelte';
	import SectionFrame from '$lib/components/SectionFrame.svelte';

	// --- Dashboard state (simple $state, no store) ---
	let dash = $state<DashboardData>({
		db_available: true,
		arm_online: false,
		active_jobs: [],
		system_info: null,
		drives_online: 0,
		drive_names: {},
		notification_count: 0,
		ripping_enabled: true,
		makemkv_key_valid: null,
		makemkv_key_checked_at: null,
		transcoder_online: false,
		transcoder_stats: null,
		transcoder_system_stats: null,
		active_transcodes: [],
		system_stats: null,
		transcoder_info: null
	});
	let dashReady = $state(false);
	let dashError = $state<string | null>(null);

	let dismissedJobIds = $state(new Set<number>());
	let scanningJobs = $derived(
		dash.active_jobs.filter(j => j.status?.toLowerCase() === 'identifying')
	);
	let waitingJobs = $derived(
		dash.active_jobs.filter(j => j.status?.toLowerCase() === 'waiting' && !dismissedJobIds.has(j.job_id))
	);
	let nonWaitingActiveJobs = $derived(dash.active_jobs.filter(j => {
		const s = j.status?.toLowerCase();
		return s !== 'waiting' && s !== 'transcoding' && s !== 'waiting_transcode' && s !== 'identifying';
	}));

	let progressMap = $state<Record<number, RipProgress>>({});

	function dismissJob(jobId: number) {
		dismissedJobIds = new Set([...dismissedJobIds, jobId]);
	}

	async function refreshDashboard() {
		try {
			dash = await fetchDashboard();
			dashReady = true;
			dashError = null;
		} catch (e) {
			dashError = e instanceof Error ? e.message : 'Unknown error';
		}
	}

	function overallProgress(p: RipProgress | undefined): number | null {
		if (!p || p.progress == null) return null;
		const total = p.tracks_total > 0 ? p.tracks_total : (p.no_of_titles ?? 0);
		if (total > 0 && p.tracks_ripped > 0) {
			// Per-track progress: some tracks done, current track partially complete
			if (p.tracks_ripped >= total) return 100;
			return ((p.tracks_ripped + p.progress / 100) / total) * 100;
		}
		// No tracks ripped yet or "all" mode (folder imports) — use raw
		// MakeMKV progress directly as overall percentage
		return p.progress;
	}

	async function pollProgress() {
		const rippingJobs = dash.active_jobs.filter(j => j.status?.toLowerCase() === 'ripping');
		if (rippingJobs.length === 0) {
			progressMap = {};
			return;
		}
		const entries = await Promise.allSettled(
			rippingJobs.map(async (j) => {
				const prog = await fetchJobProgress(j.job_id);
				return [j.job_id, prog] as const;
			})
		);
		const newMap: Record<number, RipProgress> = {};
		for (const entry of entries) {
			if (entry.status === 'fulfilled') {
				newMap[entry.value[0]] = entry.value[1];
			}
		}
		progressMap = newMap;
	}

	// --- Jobs section state ---
	let jobsData = $state<JobListResponse | null>(null);
	let jobsStats = $state<JobStats | null>(null);
	let jobsError = $state<string | null>(null);
	let jobsLoading = $state(true);

	let page = $state(1);
	let perPage = $state(25);
	let statusFilter = $state('');
	let videoTypeFilter = $state('');
	let disctypeFilter = $state('');
	let daysFilter = $state<number | undefined>(undefined);
	let searchQuery = $state('');
	let viewMode = $state<'card' | 'table'>('card');

	// Sorting
	let sortBy = $state('start_time');
	let sortDir = $state<'asc' | 'desc'>('desc');

	// Selection
	let selectedJobs = $state<Set<number>>(new Set());

	// Gear menu
	let gearOpen = $state(false);
	let bulkBusy = $state(false);
	let bulkFeedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);

	// Derived
	let allVisibleSelected = $derived(
		jobsData !== null && jobsData.jobs.length > 0 && jobsData.jobs.every((j) => selectedJobs.has(j.job_id))
	);

	let searchTimeout: ReturnType<typeof setTimeout>;

	function jobFilterParams() {
		return {
			search: searchQuery || undefined,
			video_type: videoTypeFilter || undefined,
			disctype: disctypeFilter || undefined,
			days: daysFilter
		};
	}

	async function loadJobs() {
		if (!jobsData) jobsLoading = true;
		jobsError = null;
		selectedJobs = new Set();
		try {
			const fp = jobFilterParams();
			const [jobsResult, statsResult] = await Promise.all([
				fetchJobs({
					page,
					per_page: perPage,
					status: statusFilter || undefined,
					sort_by: sortBy,
					sort_dir: sortDir,
					...fp
				}),
				fetchJobStats(fp)
			]);
			jobsData = jobsResult;
			jobsStats = statsResult;
		} catch (e) {
			jobsError = e instanceof Error ? e.message : 'Failed to load jobs';
		} finally {
			jobsLoading = false;
		}
	}

	function onSearch(e: Event) {
		const val = (e.target as HTMLInputElement).value;
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			searchQuery = val;
			page = 1;
			loadJobs();
		}, 300);
	}

	function setStatusFilter(value: string) {
		statusFilter = value;
		page = 1;
		loadJobs();
	}

	function setVideoTypeFilter(value: string) {
		videoTypeFilter = value;
		page = 1;
		loadJobs();
	}

	function setDisctypeFilter(value: string) {
		disctypeFilter = value;
		page = 1;
		loadJobs();
	}

	function setDaysFilter(value: number | undefined) {
		daysFilter = value;
		page = 1;
		loadJobs();
	}

	function toggleSort(col: string) {
		if (sortBy === col) {
			sortDir = sortDir === 'desc' ? 'asc' : 'desc';
		} else {
			sortBy = col;
			sortDir = 'desc';
		}
		loadJobs();
	}

	function sortIcon(col: string): string {
		if (sortBy !== col) return '\u21C5';
		return sortDir === 'desc' ? '\u25BC' : '\u25B2';
	}

	function toggleSelect(jobId: number, selected: boolean) {
		if (selected) {
			selectedJobs.add(jobId);
		} else {
			selectedJobs.delete(jobId);
		}
		selectedJobs = new Set(selectedJobs);
	}

	function toggleSelectAll() {
		if (!jobsData) return;
		if (allVisibleSelected) {
			selectedJobs = new Set();
		} else {
			selectedJobs = new Set(jobsData.jobs.map((j) => j.job_id));
		}
	}

	async function handleBulkAction(
		action: 'delete' | 'purge',
		params: { job_ids?: number[]; status?: string },
		description: string
	) {
		if (!confirm(`Are you sure you want to ${description}?`)) return;
		bulkBusy = true;
		bulkFeedback = null;
		gearOpen = false;
		try {
			if (action === 'delete') {
				const result = await bulkDeleteJobs(params);
				bulkFeedback = {
					type: result.errors.length > 0 ? 'error' : 'success',
					message:
						result.errors.length > 0
							? `Deleted ${result.deleted}, but ${result.errors.length} error(s)`
							: `Deleted ${result.deleted} job(s)`
				};
			} else {
				const result = await bulkPurgeJobs(params);
				bulkFeedback = {
					type: result.errors.length > 0 ? 'error' : 'success',
					message:
						result.errors.length > 0
							? `Purged ${result.purged}, but ${result.errors.length} error(s)`
							: `Purged ${result.purged} job(s)`
				};
			}
			await loadJobs();
		} catch (e) {
			bulkFeedback = {
				type: 'error',
				message: e instanceof Error ? e.message : 'Bulk action failed'
			};
		} finally {
			bulkBusy = false;
		}
	}

	function goPage(p: number) {
		page = p;
		loadJobs();
	}

	// Pill classes
	const pillBase = 'px-2.5 py-1 rounded-md text-xs font-semibold cursor-pointer transition-colors';
	const pillActive =
		'bg-primary/20 text-primary-text dark:bg-primary/25 dark:text-primary-text-dark outline outline-2 outline-primary/40';
	const pillInactive =
		'bg-primary/5 text-gray-500 hover:bg-primary/10 dark:bg-primary/10 dark:text-gray-400 hover:dark:bg-primary/15';

	// Stats card configs
	const statsCards = [
		{ key: 'total' as const, label: 'Total', filter: '', border: 'border-l-indigo-500', bg: 'bg-indigo-50 dark:bg-indigo-900/20', text: 'text-indigo-700 dark:text-indigo-300' },
		{ key: 'active' as const, label: 'Active', filter: 'active', border: 'border-l-blue-500', bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-700 dark:text-blue-300' },
		{ key: 'success' as const, label: 'Success', filter: 'success', border: 'border-l-green-500', bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-700 dark:text-green-300' },
		{ key: 'fail' as const, label: 'Failed', filter: 'fail', border: 'border-l-red-500', bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-700 dark:text-red-300' },
		{ key: 'waiting' as const, label: 'Waiting', filter: 'waiting', border: 'border-l-amber-500', bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-700 dark:text-amber-300' }
	];

	// Disc type mapping
	const discTypes = [
		{ label: 'All', value: '' },
		{ label: 'Blu-ray', value: 'bluray' },
		{ label: 'DVD', value: 'dvd' },
		{ label: 'CD', value: 'music' },
		{ label: 'Data', value: 'data' }
	];

	const daysOptions = [
		{ label: 'All Time', value: undefined as number | undefined },
		{ label: '7 days', value: 7 },
		{ label: '30 days', value: 30 },
		{ label: '90 days', value: 90 }
	];

	// Sortable columns
	const columns = [
		{ key: 'title', label: 'Title', sortable: true },
		{ key: 'year', label: 'Year', sortable: true },
		{ key: 'status', label: 'Status', sortable: true },
		{ key: 'video_type', label: 'Type', sortable: true },
		{ key: 'disctype', label: 'Disc', sortable: true },
		{ key: 'devpath', label: 'Device', sortable: true },
		{ key: 'start_time', label: 'Started', sortable: true },
		{ key: 'actions', label: 'Actions', sortable: false }
	];

	onMount(() => {
		let stopped = false;

		async function pollDashboard() {
			while (!stopped) {
				await refreshDashboard();
				await new Promise((r) => setTimeout(r, 5000));
			}
		}

		async function pollJobs() {
			while (!stopped) {
				await loadJobs();
				await new Promise((r) => setTimeout(r, 10000));
			}
		}

		async function pollProgressLoop() {
			while (!stopped) {
				await pollProgress();
				await new Promise((r) => setTimeout(r, 3000));
			}
		}

		pollDashboard();
		pollJobs();
		pollProgressLoop();
		return () => { stopped = true; };
	});
</script>

<svelte:head>
	<title>ARM - Dashboard</title>
</svelte:head>

<!-- Close gear menu on click outside -->
<svelte:window onclick={() => (gearOpen = false)} />

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
	</div>

	<!-- Global pause banner -->
	{#if dashReady && !dash.ripping_enabled}
		<div class="flex items-center gap-3 rounded-lg border border-amber-300 bg-amber-50 p-4 dark:border-amber-700 dark:bg-amber-900/20">
			<div class="h-3 w-3 shrink-0 rounded-full bg-amber-500"></div>
			<div>
				<p class="font-medium text-amber-800 dark:text-amber-300">Ripping Paused</p>
				<p class="text-sm text-amber-700 dark:text-amber-400">New discs will wait for manual start. Click "Start Ripping" on individual jobs or toggle "Auto-Start" to resume.</p>
			</div>
		</div>
	{/if}

	<!-- API error (backend unreachable) -->
	{#if dashError}
		<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
			Failed to reach backend: {dashError}
		</div>
	{/if}

	<!-- Disc review (waiting jobs) -->
	{#if waitingJobs.length > 0}
		<section>
			<SectionFrame variant="full" accent="var(--color-primary)" label="WAITING FOR REVIEW — {waitingJobs.length} DISC{waitingJobs.length > 1 ? 'S' : ''}">
				<div class="grid gap-4">
					{#each waitingJobs as job (job.job_id)}
						<DiscReviewWidget {job} driveNames={dash.drive_names} paused={!dash.ripping_enabled} onrefresh={refreshDashboard} ondismiss={() => dismissJob(job.job_id)} />
					{/each}
				</div>
			</SectionFrame>
		</section>
	{/if}

	<!-- Scanning -->
	{#if scanningJobs.length > 0}
		<section>
			<SectionFrame variant="full" accent="var(--color-cyan-500, #06b6d4)" label="SCANNING — {scanningJobs.length} {scanningJobs.length === 1 ? 'DISC' : 'DISCS'}">
				<div class="space-y-2">
					{#each scanningJobs as job (job.job_id)}
						<ActiveJobRow {job} driveNames={dash.drive_names} />
					{/each}
				</div>
			</SectionFrame>
		</section>
	{/if}

	<!-- Active rips -->
	{#if nonWaitingActiveJobs.length > 0}
		<section>
			<SectionFrame variant="full" accent="var(--color-primary)" label="ACTIVE RIPS — {nonWaitingActiveJobs.length} IN PROGRESS">
				<div class="space-y-2">
					{#each nonWaitingActiveJobs as job (job.job_id)}
						<ActiveJobRow {job} driveNames={dash.drive_names} progress={overallProgress(progressMap[job.job_id])} progressStage={progressMap[job.job_id]?.stage} />
					{/each}
				</div>
			</SectionFrame>
		</section>
	{/if}

	<!-- Active transcodes -->
	{#if dash.active_transcodes.length > 0}
		<section>
			<SectionFrame variant="full" accent="var(--color-primary)" label="TRANSCODING — {dash.active_transcodes.length} ACTIVE">
				<div class="space-y-2">
					{#each dash.active_transcodes as tc}
						<TranscodeCard job={tc} />
					{/each}
				</div>
			</SectionFrame>
		</section>
	{/if}

	<!-- Idle state -->
	{#if dashReady && waitingJobs.length === 0 && nonWaitingActiveJobs.length === 0 && dash.active_transcodes.length === 0}
		<section>
			<div class="rounded-lg border border-primary/20 bg-surface p-6 text-center shadow-xs dark:border-primary/20 dark:bg-surface-dark">
				<svg class="mx-auto h-12 w-12 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
					<circle cx="12" cy="12" r="10" />
					<circle cx="12" cy="12" r="3" />
					<circle cx="12" cy="12" r="6.5" stroke-width="0.75" opacity="0.4" />
				</svg>
				<p class="mt-3 text-sm font-medium text-gray-500 dark:text-gray-400">No active rips or transcodes</p>
				<p class="mt-1 text-xs text-gray-400 dark:text-gray-500">Insert a disc to get started — {dash.drives_online} drive{dash.drives_online !== 1 ? 's' : ''} online{#if !dash.arm_online}, ARM offline{/if}{#if !dash.transcoder_online}, transcoder offline{/if}</p>
			</div>
		</section>
	{/if}

	<!-- All Jobs -->
	<section id="all-jobs" class="space-y-4">
			<div class="flex flex-wrap items-center justify-between gap-4">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white">All Jobs</h2>
				<div class="flex gap-2">
					<button
						onclick={() => viewMode = 'card'}
						class="rounded-lg px-3 py-1.5 text-sm {viewMode === 'card' ? 'bg-primary text-on-primary' : 'bg-primary/15 text-gray-700 dark:bg-primary/15 dark:text-gray-300'}"
					>Cards</button>
					<button
						onclick={() => viewMode = 'table'}
						class="rounded-lg px-3 py-1.5 text-sm {viewMode === 'table' ? 'bg-primary text-on-primary' : 'bg-primary/15 text-gray-700 dark:bg-primary/15 dark:text-gray-300'}"
					>Table</button>
				</div>
			</div>

			<!-- Stats Bar -->
			{#if jobsStats}
				<div class="flex flex-wrap gap-3">
					{#each statsCards as card}
						<button
							onclick={() => setStatusFilter(card.filter)}
							class="flex min-w-[120px] flex-1 cursor-pointer items-center gap-3 rounded-lg border-l-4 {card.border} {card.bg} px-4 py-3 transition-shadow hover:shadow-md {statusFilter === card.filter ? 'ring-2 ring-primary/40' : ''}"
						>
							<div>
								<div class="text-2xl font-bold {card.text}">{jobsStats[card.key]}</div>
								<div class="text-xs font-medium text-gray-500 dark:text-gray-400">{card.label}</div>
							</div>
						</button>
					{/each}
				</div>
			{/if}

			<!-- Filter Row 1: Search | Status pills | Type pills -->
			<div class="flex flex-wrap items-center gap-3">
				<input
					type="text"
					placeholder="Search titles..."
					oninput={onSearch}
					class="lcars-input w-48 rounded-lg border border-primary/25 bg-primary/5 px-3 py-2 text-sm dark:border-primary/30 dark:bg-primary/10 dark:text-white"
				/>

				<div class="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>

				<!-- Status pills -->
				<div class="flex flex-wrap gap-1.5">
					{#each [{ label: 'All', value: '' }, { label: 'Active', value: 'active' }, { label: 'Success', value: 'success' }, { label: 'Failed', value: 'fail' }, { label: 'Waiting', value: 'waiting' }] as pill}
						<button
							onclick={() => setStatusFilter(pill.value)}
							class="{pillBase} {statusFilter === pill.value ? pillActive : pillInactive}"
						>{pill.label}</button>
					{/each}
				</div>

				<div class="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>

				<!-- Type pills -->
				<div class="flex flex-wrap gap-1.5">
					{#each [{ label: 'All', value: '' }, { label: 'Movie', value: 'movie' }, { label: 'Series', value: 'series' }, { label: 'Music', value: 'music' }] as pill}
						<button
							onclick={() => setVideoTypeFilter(pill.value)}
							class="{pillBase} {videoTypeFilter === pill.value ? pillActive : pillInactive}"
						>{pill.label}</button>
					{/each}
				</div>
			</div>

			<!-- Filter Row 2: Disc pills | Time range | Selection count | Gear menu -->
			<div class="flex flex-wrap items-center gap-3">
				<!-- Disc pills -->
				<div class="flex flex-wrap gap-1.5">
					{#each discTypes as disc}
						<button
							onclick={() => setDisctypeFilter(disc.value)}
							class="{pillBase} {disctypeFilter === disc.value ? pillActive : pillInactive}"
						>{disc.label}</button>
					{/each}
				</div>

				<div class="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>

				<!-- Time range select -->
				<select
					value={daysFilter ?? ''}
					onchange={(e) => {
						const val = (e.target as HTMLSelectElement).value;
						setDaysFilter(val ? Number(val) : undefined);
					}}
					class="lcars-input rounded-lg border border-primary/25 bg-primary/5 px-3 py-1.5 text-xs dark:border-primary/30 dark:bg-primary/10 dark:text-white"
				>
					{#each daysOptions as opt}
						<option value={opt.value ?? ''}>{opt.label}</option>
					{/each}
				</select>

				<div class="flex-1"></div>

				<!-- Selection count -->
				{#if selectedJobs.size > 0}
					<span class="text-sm font-medium text-gray-600 dark:text-gray-300">{selectedJobs.size} selected</span>
				{/if}

				<!-- Gear menu -->
				<div class="relative">
					<button
						onclick={(e: MouseEvent) => { e.stopPropagation(); gearOpen = !gearOpen; }}
						disabled={bulkBusy}
						class="{pillBase} inline-flex items-center gap-1 bg-primary/10 text-gray-700 hover:bg-primary/20 dark:bg-primary/15 dark:text-gray-300 dark:hover:bg-primary/25 disabled:opacity-50"
					>
						{#if bulkBusy}
							<span class="inline-block h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent"></span>
						{:else}
							&#9881;
						{/if}
						Actions &#9662;
					</button>

					{#if gearOpen}
						<!-- svelte-ignore a11y_click_events_have_key_events -->
						<!-- svelte-ignore a11y_no_static_element_interactions -->
						<div
							onclick={(e: MouseEvent) => e.stopPropagation()}
							class="absolute right-0 z-50 mt-1 w-56 rounded-lg border border-primary/20 bg-surface py-1 shadow-lg dark:border-primary/25 dark:bg-surface-dark"
						>
							{#if selectedJobs.size > 0}
								<div class="px-3 py-1.5 text-xs font-semibold text-gray-400 dark:text-gray-500">Selected ({selectedJobs.size})</div>
								<button
									onclick={() => handleBulkAction('delete', { job_ids: [...selectedJobs] }, `delete ${selectedJobs.size} selected job(s)`)}
									class="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-primary/5 dark:text-gray-300 dark:hover:bg-primary/10"
								>Delete Selected</button>
								<button
									onclick={() => handleBulkAction('purge', { job_ids: [...selectedJobs] }, `purge ${selectedJobs.size} selected job(s) and their files`)}
									class="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
								>Purge Selected</button>
								<div class="my-1 border-t border-gray-200 dark:border-gray-700"></div>
							{/if}

							<div class="px-3 py-1.5 text-xs font-semibold text-gray-400 dark:text-gray-500">Bulk Actions</div>
							<button
								onclick={() => handleBulkAction('delete', { status: 'fail' }, `delete all failed jobs${jobsStats?.fail ? ` (${jobsStats.fail})` : ''}`)}
								class="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-primary/5 dark:text-gray-300 dark:hover:bg-primary/10"
							>Delete All Failed{#if jobsStats?.fail} ({jobsStats.fail}){/if}</button>
							<button
								onclick={() => handleBulkAction('purge', { status: 'fail' }, `purge all failed jobs and their files`)}
								class="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
							>Purge All Failed</button>
							<button
								onclick={() => handleBulkAction('delete', { status: 'success' }, `delete all successful jobs${jobsStats?.success ? ` (${jobsStats.success})` : ''}`)}
								class="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-primary/5 dark:text-gray-300 dark:hover:bg-primary/10"
							>Delete All Successful{#if jobsStats?.success} ({jobsStats.success}){/if}</button>
						</div>
					{/if}
				</div>
			</div>

			<!-- Bulk feedback banner -->
			{#if bulkFeedback}
				<div class="rounded-lg border px-4 py-3 text-sm {bulkFeedback.type === 'success' ? 'border-green-200 bg-green-50 text-green-700 dark:border-green-800 dark:bg-green-900/20 dark:text-green-400' : 'border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400'}">
					{bulkFeedback.message}
					<button onclick={() => (bulkFeedback = null)} class="ml-2 font-bold opacity-60 hover:opacity-100">&times;</button>
				</div>
			{/if}

			{#if jobsError}
				<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
					{jobsError}
				</div>
			{:else if jobsLoading}
				<div class="py-8 text-center text-gray-400">Loading...</div>
			{:else if jobsData}
				{#if viewMode === 'table'}
					<div class="overflow-x-auto rounded-lg border border-primary/20 dark:border-primary/20">
						<table class="w-full text-left text-sm">
							<thead class="bg-page text-gray-600 dark:bg-primary/5 dark:text-gray-400">
								<tr>
									<th class="px-4 py-3 w-8">
										<input
											type="checkbox"
											checked={allVisibleSelected}
											onchange={toggleSelectAll}
											class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary dark:border-gray-600 dark:bg-gray-700"
										/>
									</th>
									{#each columns as col}
										<th class="px-4 py-3 font-medium">
											{#if col.sortable}
												<button
													onclick={() => toggleSort(col.key)}
													class="inline-flex items-center gap-1 hover:text-primary-text dark:hover:text-primary-text-dark"
												>
													{col.label}
													<span class="text-xs opacity-60">{sortIcon(col.key)}</span>
												</button>
											{:else}
												{col.label}
											{/if}
										</th>
									{/each}
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
								{#each jobsData.jobs as job (job.job_id)}
									<JobRow
										{job}
										onaction={loadJobs}
										selected={selectedJobs.has(job.job_id)}
										onselect={toggleSelect}
									/>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
						{#each jobsData.jobs as job (job.job_id)}
							<JobCard {job} driveNames={dash.drive_names} progress={overallProgress(progressMap[job.job_id])} progressStage={progressMap[job.job_id]?.stage} />
						{/each}
					</div>
				{/if}

				<!-- Pagination -->
				{#if jobsData.pages > 1}
					<div class="flex items-center justify-between">
						<p class="text-sm text-gray-500 dark:text-gray-400">
							Showing {(jobsData.page - 1) * jobsData.per_page + 1}&ndash;{Math.min(jobsData.page * jobsData.per_page, jobsData.total)} of {jobsData.total}
						</p>
						<div class="flex gap-1">
							<button
								disabled={jobsData.page <= 1}
								onclick={() => goPage(jobsData!.page - 1)}
								class="rounded-sm px-3 py-1 text-sm disabled:opacity-50 bg-primary/15 dark:bg-primary/15 dark:text-gray-300"
							>Prev</button>
							{#each Array.from({ length: jobsData.pages }, (_, i) => i + 1) as p}
								{#if p === jobsData.page || p === 1 || p === jobsData.pages || Math.abs(p - jobsData.page) <= 1}
									<button
										onclick={() => goPage(p)}
										class="rounded-sm px-3 py-1 text-sm {p === jobsData.page ? 'bg-primary text-on-primary' : 'bg-primary/15 dark:bg-primary/15 dark:text-gray-300'}"
									>{p}</button>
								{:else if Math.abs(p - jobsData.page) === 2}
									<span class="px-1 text-gray-400">...</span>
								{/if}
							{/each}
							<button
								disabled={jobsData.page >= jobsData.pages}
								onclick={() => goPage(jobsData!.page + 1)}
								class="rounded-sm px-3 py-1 text-sm disabled:opacity-50 bg-primary/15 dark:bg-primary/15 dark:text-gray-300"
							>Next</button>
						</div>
					</div>
				{/if}

				{#if jobsData.jobs.length === 0}
					<p class="py-8 text-center text-gray-400">No jobs found.</p>
				{/if}
			{/if}
	</section>
</div>
