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
	import JobFilterBar from '$lib/components/JobFilterBar.svelte';
	import BulkActionsMenu from '$lib/components/BulkActionsMenu.svelte';
	import JobPagination from '$lib/components/JobPagination.svelte';
	import LoadState from '$lib/components/LoadState.svelte';
	import EmptyDashboardPanel from '$lib/components/EmptyDashboardPanel.svelte';
	import { fadeIn, fadeOut } from '$lib/transitions';
	import { fade } from 'svelte/transition';
	import { transcoderEnabled } from '$lib/stores/config';

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
	let dashLoading = $state(true);
	let dashError = $state<Error | null>(null);

	let dismissedJobIds = $state(new Set<number>());
	let scanningJobs = $derived(
		dash.active_jobs.filter(j => {
			const s = j.status?.toLowerCase();
			return s === 'identifying' || s === 'ready';
		})
	);
	let waitingJobs = $derived(
		dash.active_jobs.filter(j => j.status?.toLowerCase() === 'waiting' && !dismissedJobIds.has(j.job_id))
	);
	let nonWaitingActiveJobs = $derived(dash.active_jobs.filter(j => {
		const s = j.status?.toLowerCase();
		return s !== 'waiting' && s !== 'transcoding' && s !== 'waiting_transcode'
			&& s !== 'identifying' && s !== 'ready'
			&& s !== 'copying' && s !== 'ejecting';
	}));
	let finishingJobs = $derived(dash.active_jobs.filter(j => {
		const s = j.status?.toLowerCase();
		if (!$transcoderEnabled && s === 'waiting_transcode') return false;
		return s === 'copying' || s === 'ejecting' || s === 'waiting_transcode';
	}));

	let progressMap = $state<Record<number, RipProgress>>({});

	function dismissJob(jobId: number) {
		dismissedJobIds = new Set([...dismissedJobIds, jobId]);
	}

	async function refreshDashboard() {
		try {
			dash = await fetchDashboard();
			dashError = null;
		} catch (e) {
			dashError = e instanceof Error ? e : new Error('Unknown error');
		} finally {
			dashLoading = false;
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
	let jobsError = $state<Error | null>(null);
	let jobsLoading = $state(true);
	let pageReady = $derived(!dashLoading && !jobsLoading);

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
			jobsError = e instanceof Error ? e : new Error('Failed to load jobs');
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

	function applyFilterAndReload<T>(setter: (v: T) => void) {
		return (value: T) => { setter(value); page = 1; loadJobs(); };
	}

	const setStatusFilter = applyFilterAndReload<string>(v => statusFilter = v);
	const setVideoTypeFilter = applyFilterAndReload<string>(v => videoTypeFilter = v);
	const setDisctypeFilter = applyFilterAndReload<string>(v => disctypeFilter = v);
	const setDaysFilter = applyFilterAndReload<number | undefined>(v => daysFilter = v);

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

		function poll(fn: () => Promise<void>, intervalMs: number) {
			(async () => { while (!stopped) { await fn(); await new Promise(r => setTimeout(r, intervalMs)); } })();
		}

		poll(refreshDashboard, 5000);
		poll(loadJobs, 10000);
		poll(pollProgress, 3000);
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

	<!-- Job counts -->
	<div class="flex flex-wrap gap-3">
		{#each [
			{ key: 'total' as const, label: 'Total', border: 'border-l-indigo-500', bg: 'bg-indigo-50 dark:bg-indigo-900/20', text: 'text-indigo-700 dark:text-indigo-300' },
			{ key: 'active' as const, label: 'Active', border: 'border-l-blue-500', bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-700 dark:text-blue-300' },
			{ key: 'success' as const, label: 'Success', border: 'border-l-green-500', bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-700 dark:text-green-300' },
			{ key: 'fail' as const, label: 'Failed', border: 'border-l-red-500', bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-700 dark:text-red-300' },
			{ key: 'waiting' as const, label: 'Waiting', border: 'border-l-amber-500', bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-700 dark:text-amber-300' }
		] as card}
			<div class="flex min-w-[100px] flex-1 items-center gap-3 rounded-lg border-l-4 {card.border} {card.bg} px-4 py-3">
				<div>
					<div class="text-2xl font-bold {card.text}">{jobsStats?.[card.key] ?? '—'}</div>
					<div class="text-xs font-medium text-gray-500 dark:text-gray-400">{card.label}</div>
				</div>
			</div>
		{/each}
	</div>

	<!-- Global pause banner -->
	{#if !dashLoading && !dash.ripping_enabled}
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
			Failed to reach backend: {dashError.message}
		</div>
	{/if}

	<!-- Disc review (waiting jobs) -->
	{#if waitingJobs.length > 0}
		<section in:fade={fadeIn} out:fade={fadeOut}>
			<SectionFrame variant="full" accent="var(--color-primary)" label="WAITING FOR REVIEW — {waitingJobs.length} DISC{waitingJobs.length > 1 ? 'S' : ''}">
				<div class="grid gap-4">
					{#each waitingJobs as job (job.job_id)}
						<div in:fade|local={fadeIn} out:fade|local={fadeOut}>
							<DiscReviewWidget {job} driveNames={dash.drive_names} paused={!dash.ripping_enabled} onrefresh={refreshDashboard} ondismiss={() => dismissJob(job.job_id)} />
						</div>
					{/each}
				</div>
			</SectionFrame>
		</section>
	{/if}

	<!-- Scanning -->
	{#if scanningJobs.length > 0}
		<section in:fade={fadeIn} out:fade={fadeOut}>
			<SectionFrame variant="full" accent="var(--color-cyan-500, #06b6d4)" label="SCANNING — {scanningJobs.length} {scanningJobs.length === 1 ? 'DISC' : 'DISCS'}">
				<div class="space-y-2">
					{#each scanningJobs as job (job.job_id)}
						<div in:fade|local={fadeIn} out:fade|local={fadeOut}>
							<ActiveJobRow {job} driveNames={dash.drive_names} />
						</div>
					{/each}
				</div>
			</SectionFrame>
		</section>
	{/if}

	<!-- Active rips -->
	{#if nonWaitingActiveJobs.length > 0}
		<section in:fade={fadeIn} out:fade={fadeOut}>
			<SectionFrame variant="full" accent="var(--color-primary)" label="ACTIVE RIPS — {nonWaitingActiveJobs.length} IN PROGRESS">
				<div class="space-y-2">
					{#each nonWaitingActiveJobs as job (job.job_id)}
						<div in:fade|local={fadeIn} out:fade|local={fadeOut}>
							<ActiveJobRow {job} driveNames={dash.drive_names} progress={overallProgress(progressMap[job.job_id])} progressStage={progressMap[job.job_id]?.stage} tracksRipped={progressMap[job.job_id]?.tracks_ripped} tracksTotal={progressMap[job.job_id]?.tracks_total} />
						</div>
					{/each}
				</div>
			</SectionFrame>
		</section>
	{/if}

	<!-- Finishing (copying / ejecting / waiting_transcode) -->
	{#if finishingJobs.length > 0}
		<section in:fade={fadeIn} out:fade={fadeOut}>
			<SectionFrame variant="full" accent="var(--color-amber-500, #f59e0b)" label="FINISHING — {finishingJobs.length} {finishingJobs.length === 1 ? 'JOB' : 'JOBS'}">
				<div class="space-y-2">
					{#each finishingJobs as job (job.job_id)}
						<div in:fade|local={fadeIn} out:fade|local={fadeOut}>
							<ActiveJobRow {job} driveNames={dash.drive_names} />
						</div>
					{/each}
				</div>
			</SectionFrame>
		</section>
	{/if}

	<!-- Active transcodes -->
	{#if $transcoderEnabled && dash.active_transcodes.length > 0}
		<section in:fade={fadeIn} out:fade={fadeOut}>
			<SectionFrame variant="full" accent="var(--color-primary)" label="TRANSCODING — {dash.active_transcodes.length} ACTIVE">
				<div class="space-y-2">
					{#each dash.active_transcodes as tc (tc.id)}
						<div in:fade|local={fadeIn} out:fade|local={fadeOut}>
							{#if tc.arm_job_id}
								<a href="/jobs/{tc.arm_job_id}" class="block transition-opacity hover:opacity-80">
									<TranscodeCard job={tc} />
								</a>
							{:else}
								<TranscodeCard job={tc} />
							{/if}
						</div>
					{/each}
				</div>
			</SectionFrame>
		</section>
	{/if}

	<!-- Idle state -->
	{#if pageReady && scanningJobs.length === 0 && waitingJobs.length === 0 && nonWaitingActiveJobs.length === 0 && finishingJobs.length === 0 && dash.active_transcodes.length === 0}
		<div in:fade={fadeIn}>
			<EmptyDashboardPanel
				drivesOnline={dash.drives_online}
				armOnline={dash.arm_online}
				transcoderOnline={dash.transcoder_online}
			/>
		</div>
	{/if}

	<!-- All Jobs -->
	<section id="all-jobs" class="space-y-4">
			<!-- Controls panel -->
			<div class="rounded-lg border border-primary/20 bg-surface shadow-xs dark:border-primary/20 dark:bg-surface-dark">
				<!-- Header: Title + View toggle + Bulk actions -->
				<div class="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white">All Jobs</h2>
					<div class="flex items-center gap-3">
						<div class="flex gap-1">
							<button
								onclick={() => viewMode = 'card'}
								class="rounded-md px-3 py-1.5 text-xs font-medium {viewMode === 'card' ? 'bg-primary text-on-primary' : 'bg-primary/10 text-gray-600 hover:bg-primary/15 dark:bg-primary/15 dark:text-gray-300'}"
							>Cards</button>
							<button
								onclick={() => viewMode = 'table'}
								class="rounded-md px-3 py-1.5 text-xs font-medium {viewMode === 'table' ? 'bg-primary text-on-primary' : 'bg-primary/10 text-gray-600 hover:bg-primary/15 dark:bg-primary/15 dark:text-gray-300'}"
							>Table</button>
						</div>
						<div class="h-5 w-px bg-primary/20 dark:bg-primary/20"></div>
						<BulkActionsMenu
							{selectedJobs}
							{jobsStats}
							{gearOpen}
							{bulkBusy}
							onaction={handleBulkAction}
							ontoggle={() => (gearOpen = !gearOpen)}
						/>
					</div>
				</div>

				<!-- Filters -->
				<div class="border-t border-primary/15 px-4 py-3 dark:border-primary/15">
					<JobFilterBar
						{statusFilter}
						{videoTypeFilter}
						{disctypeFilter}
						{daysFilter}
						onstatusfilter={setStatusFilter}
						onvideotypefilter={setVideoTypeFilter}
						ondisctypefilter={setDisctypeFilter}
						ondaysfilter={setDaysFilter}
						onsearch={onSearch}
					/>
				</div>

				<!-- Bulk feedback banner -->
				{#if bulkFeedback}
					<div class="border-t border-primary/15 px-4 py-3 text-sm dark:border-primary/15 {bulkFeedback.type === 'success' ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'}">
						{bulkFeedback.message}
						<button onclick={() => (bulkFeedback = null)} class="ml-2 font-bold opacity-60 hover:opacity-100">&times;</button>
					</div>
				{/if}
			</div>

			<div style="min-height: 60vh;">
			<LoadState
				data={jobsData?.jobs}
				loading={jobsLoading}
				error={jobsError}
				transitionKey="dashboard-recent-jobs"
			>
				{#snippet loadingSlot()}
					{#if viewMode === 'table'}
						<div class="overflow-x-auto rounded-lg border border-primary/20 dark:border-primary/20">
							<table class="responsive-table w-full text-left text-sm">
								<thead class="bg-page text-gray-600 dark:bg-primary/5 dark:text-gray-400">
									<tr>
										<th class="px-4 py-3 w-8"></th>
										{#each columns as col}
											<th class="px-4 py-3 font-medium">{col.label}</th>
										{/each}
									</tr>
								</thead>
								<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
									{#each { length: 25 } as _}
										<JobRow />
									{/each}
								</tbody>
							</table>
						</div>
					{:else}
						<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
							{#each { length: 6 } as _}
								<JobCard />
							{/each}
						</div>
					{/if}
				{/snippet}
				{#snippet ready(jobs)}
					{#if viewMode === 'table'}
						<div class="overflow-x-auto rounded-lg border border-primary/20 dark:border-primary/20">
							<table class="responsive-table w-full text-left text-sm">
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
									{#each jobs as job (job.job_id)}
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
							{#each jobs as job (job.job_id)}
								<JobCard {job} driveNames={dash.drive_names} progress={overallProgress(progressMap[job.job_id])} progressStage={progressMap[job.job_id]?.stage} />
							{/each}
						</div>
					{/if}

					<!-- Pagination -->
					<JobPagination
						page={jobsData!.page}
						pages={jobsData!.pages}
						perPage={jobsData!.per_page}
						total={jobsData!.total}
						onpage={goPage}
					/>
				{/snippet}
				{#snippet empty()}
					<p class="py-8 text-center text-gray-400">No jobs found.</p>
				{/snippet}
			</LoadState>
			</div>
	</section>
</div>
