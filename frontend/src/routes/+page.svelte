<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchDashboard } from '$lib/api/dashboard';
	import { fetchJobs } from '$lib/api/jobs';
	import { fetchJobProgress } from '$lib/api/jobs';
	import type { RipProgress } from '$lib/api/jobs';
	import type { DashboardData, JobListResponse } from '$lib/types/arm';
	import DiscReviewWidget from '$lib/components/DiscReviewWidget.svelte';
	import JobCard from '$lib/components/JobCard.svelte';
	import JobRow from '$lib/components/JobRow.svelte';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import TranscodeCard from '$lib/components/TranscodeCard.svelte';
	import SectionFrame from '$lib/components/SectionFrame.svelte';
	import JobStatsCard from '$lib/components/JobStatsCard.svelte';
	import FolderImportWizard from '$lib/components/FolderImportWizard.svelte';

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
		transcoder_online: false,
		transcoder_stats: null,
		transcoder_system_stats: null,
		active_transcodes: [],
		system_stats: null,
		transcoder_info: null
	});
	let dashReady = $state(false);
	let dashError = $state<string | null>(null);

	let showImportWizard = $state(false);

	let dismissedJobIds = $state(new Set<number>());
	let waitingJobs = $derived(
		dash.active_jobs.filter(j => j.status?.toLowerCase() === 'waiting' && !dismissedJobIds.has(j.job_id))
	);
	let nonWaitingActiveJobs = $derived(dash.active_jobs.filter(j => {
		const s = j.status?.toLowerCase();
		return s !== 'waiting' && s !== 'transcoding' && s !== 'waiting_transcode';
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
		if (total > 0) {
			if (p.tracks_ripped >= total) return 100;
			return ((p.tracks_ripped + p.progress / 100) / total) * 100;
		}
		// No tracks in DB yet and no title count — show indeterminate bar.
		// MakeMKV resets PRGV per phase, so raw progress can spike to 100%
		// during scan completion before any actual ripping starts.
		return null;
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
	let jobsError = $state<string | null>(null);
	let jobsLoading = $state(true);

	let page = $state(1);
	let perPage = $state(25);
	let statusFilter = $state('');
	let videoTypeFilter = $state('');
	let searchQuery = $state('');
	let viewMode = $state<'card' | 'table'>('card');

	let searchTimeout: ReturnType<typeof setTimeout>;

	async function loadJobs() {
		if (!jobsData) jobsLoading = true;
		jobsError = null;
		try {
			jobsData = await fetchJobs({
				page,
				per_page: perPage,
				status: statusFilter || undefined,
				search: searchQuery || undefined,
				video_type: videoTypeFilter || undefined
			});
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

	function setFilter(type: 'status' | 'videoType', value: string) {
		if (type === 'status') statusFilter = value;
		else videoTypeFilter = value;
		page = 1;
		loadJobs();
	}

	function goPage(p: number) {
		page = p;
		loadJobs();
	}

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

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
	</div>

	<div class="mb-4 flex justify-end">
		<button
			type="button"
			onclick={() => showImportWizard = true}
			class="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-on-primary hover:bg-primary/90"
		>
			Import Folder
		</button>
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
			<SectionFrame variant="full" accent="#f90" label="WAITING FOR REVIEW — {waitingJobs.length} DISC{waitingJobs.length > 1 ? 'S' : ''}">
				<div class="grid gap-4">
					{#each waitingJobs as job (job.job_id)}
						<DiscReviewWidget {job} driveNames={dash.drive_names} paused={!dash.ripping_enabled} onrefresh={refreshDashboard} ondismiss={() => dismissJob(job.job_id)} />
					{/each}
				</div>
			</SectionFrame>
		</section>
	{/if}

	<!-- Active rips -->
	{#if nonWaitingActiveJobs.length > 0}
		<section>
			<SectionFrame variant="full" accent="#99f" label="ACTIVE RIPS — {nonWaitingActiveJobs.length} IN PROGRESS">
				<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
					{#each nonWaitingActiveJobs as job (job.job_id)}
						<JobCard {job} driveNames={dash.drive_names} progress={overallProgress(progressMap[job.job_id])} progressStage={progressMap[job.job_id]?.stage} />
					{/each}
				</div>
			</SectionFrame>
		</section>
	{/if}

	<!-- Active transcodes -->
	{#if dash.active_transcodes.length > 0}
		<section>
			<SectionFrame variant="full" accent="#c9c" label="TRANSCODING — {dash.active_transcodes.length} ACTIVE">
				<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
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

	<!-- Ripping Statistics -->
	<JobStatsCard />

	<!-- All Jobs -->
	<section class="space-y-4">
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

			<!-- Filters -->
			<div class="flex flex-wrap gap-3">
				<input
					type="text"
					placeholder="Search titles..."
					oninput={onSearch}
					class="lcars-input rounded-lg border border-primary/25 bg-primary/5 px-3 py-2 text-sm dark:border-primary/30 dark:bg-primary/10 dark:text-white"
				/>
				<select
					value={statusFilter}
					onchange={(e) => setFilter('status', (e.target as HTMLSelectElement).value)}
					class="lcars-input rounded-lg border border-primary/25 bg-primary/5 px-3 py-2 text-sm dark:border-primary/30 dark:bg-primary/10 dark:text-white"
				>
					<option value="">All Statuses</option>
					<option value="active">Active</option>
					<option value="ripping">Ripping</option>
					<option value="transcoding">Transcoding</option>
					<option value="success">Success</option>
					<option value="fail">Failed</option>
				</select>
				<select
					value={videoTypeFilter}
					onchange={(e) => setFilter('videoType', (e.target as HTMLSelectElement).value)}
					class="lcars-input rounded-lg border border-primary/25 bg-primary/5 px-3 py-2 text-sm dark:border-primary/30 dark:bg-primary/10 dark:text-white"
				>
					<option value="">All Types</option>
					<option value="movie">Movie</option>
					<option value="series">Series</option>
					<option value="music">Music</option>
				</select>
			</div>

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
									<th class="px-4 py-3 font-medium">Title</th>
									<th class="px-4 py-3 font-medium">Year</th>
									<th class="px-4 py-3 font-medium">Status</th>
									<th class="px-4 py-3 font-medium">Type</th>
									<th class="px-4 py-3 font-medium">Disc</th>
									<th class="px-4 py-3 font-medium">Drive</th>
									<th class="px-4 py-3 font-medium">Started</th>
									<th class="px-4 py-3 font-medium">Actions</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
								{#each jobsData.jobs as job (job.job_id)}
									<JobRow {job} driveNames={dash.drive_names} onaction={loadJobs} />
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
							Showing {(jobsData.page - 1) * jobsData.per_page + 1}–{Math.min(jobsData.page * jobsData.per_page, jobsData.total)} of {jobsData.total}
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

<FolderImportWizard
	open={showImportWizard}
	onclose={() => showImportWizard = false}
	oncreated={() => { showImportWizard = false; refreshDashboard(); }}
/>
