<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchDashboard, setRippingEnabled } from '$lib/api/dashboard';
	import { fetchJobs } from '$lib/api/jobs';
	import { fetchJobProgress } from '$lib/api/jobs';
	import type { RipProgress } from '$lib/api/jobs';
	import type { DashboardData, JobListResponse } from '$lib/types/arm';
	import DiscReviewWidget from '$lib/components/DiscReviewWidget.svelte';
	import JobCard from '$lib/components/JobCard.svelte';
	import JobRow from '$lib/components/JobRow.svelte';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import TranscodeCard from '$lib/components/TranscodeCard.svelte';
	import LcarsFrame from '$lib/components/LcarsFrame.svelte';

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
	let togglingPause = $state(false);

	async function toggleRipping() {
		togglingPause = true;
		try {
			await setRippingEnabled(!dash.ripping_enabled);
			await refreshDashboard();
		} catch {
			// next poll will reconcile
		} finally {
			togglingPause = false;
		}
	}
	let dashReady = $state(false);
	let dashError = $state<string | null>(null);

	let dismissedJobIds = $state(new Set<number>());
	let waitingJobs = $derived(
		dash.active_jobs.filter(j => j.status?.toLowerCase() === 'waiting' && !dismissedJobIds.has(j.job_id))
	);
	let nonWaitingActiveJobs = $derived(dash.active_jobs.filter(j => j.status?.toLowerCase() !== 'waiting'));

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
	let viewMode = $state<'card' | 'table'>('table');

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
		<!-- Accepting Discs toggle -->
		{#if dashReady && dash.db_available}
			<button
				onclick={toggleRipping}
				disabled={togglingPause}
				class="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors {dash.ripping_enabled
					? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
					: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'}"
			>
				<div class="relative h-5 w-9 rounded-full transition-colors {dash.ripping_enabled ? 'bg-emerald-500' : 'bg-amber-500'}">
					<div class="absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform {dash.ripping_enabled ? 'translate-x-4' : 'translate-x-0.5'}"></div>
				</div>
				{dash.ripping_enabled ? 'Auto-Start' : 'Paused'}
			</button>
		{/if}
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

	<!-- Service status banners -->
	{#if dashReady && !dash.db_available}
		<div class="flex items-center gap-3 rounded-lg border border-yellow-300 bg-yellow-50 p-4 dark:border-yellow-700 dark:bg-yellow-900/20">
			<div class="h-3 w-3 shrink-0 rounded-full bg-yellow-500"></div>
			<div>
				<p class="font-medium text-yellow-800 dark:text-yellow-300">ARM Database Unavailable</p>
				<p class="text-sm text-yellow-700 dark:text-yellow-400">Cannot connect to the ARM database. Check that the database file is mounted and the path is correct.</p>
			</div>
		</div>
	{/if}

	{#if dashReady && !dash.arm_online}
		<div class="flex items-center gap-3 rounded-lg border border-orange-300 bg-orange-50 p-4 dark:border-orange-700 dark:bg-orange-900/20">
			<div class="h-3 w-3 shrink-0 rounded-full bg-orange-500"></div>
			<div>
				<p class="font-medium text-orange-800 dark:text-orange-300">ARM Service Unreachable</p>
				<p class="text-sm text-orange-700 dark:text-orange-400">Cannot reach the ARM ripping service API. Check that ARM_UI_ARM_URL is configured correctly and that the service is running.</p>
			</div>
		</div>
	{/if}

	{#if dashReady && !dash.transcoder_online}
		<div class="flex items-center gap-3 rounded-lg border border-orange-300 bg-orange-50 p-4 dark:border-orange-700 dark:bg-orange-900/20">
			<div class="h-3 w-3 shrink-0 rounded-full bg-orange-500"></div>
			<div>
				<p class="font-medium text-orange-800 dark:text-orange-300">Transcoder Service Unreachable</p>
				<p class="text-sm text-orange-700 dark:text-orange-400">Cannot reach the transcoder service API. Check that ARM_UI_TRANSCODER_URL is configured correctly and that the service is running.</p>
			</div>
		</div>
	{/if}

	<!-- Stats cards -->
	<div class="grid grid-cols-3 gap-4">
		<!-- Active Rips -->
		<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-light-bg dark:bg-primary-light-bg-dark/30">
					<svg class="h-5 w-5 text-primary dark:text-primary-text-dark" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<circle cx="12" cy="12" r="10" />
						<circle cx="12" cy="12" r="3" />
						<circle cx="12" cy="12" r="6.5" stroke-width="1" opacity="0.4" />
					</svg>
				</div>
				<div>
					<p class="text-sm text-gray-500 dark:text-gray-400">Active Rips</p>
					<p class="text-2xl font-bold text-gray-900 dark:text-white">
						{dash.db_available ? dash.active_jobs.length : '--'}
					</p>
				</div>
			</div>
		</div>
		<!-- Active Transcodes -->
		<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-100 dark:bg-indigo-900/30">
					<svg class="h-5 w-5 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
					</svg>
				</div>
				<div>
					<p class="text-sm text-gray-500 dark:text-gray-400">Active Transcodes</p>
					<p class="text-2xl font-bold text-gray-900 dark:text-white">
						{dashReady ? (dash.transcoder_online ? dash.active_transcodes.length : '--') : '...'}
					</p>
				</div>
			</div>
		</div>
		<!-- Drives Online -->
		<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
					<svg class="h-5 w-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
					</svg>
				</div>
				<div>
					<p class="text-sm text-gray-500 dark:text-gray-400">Drives Online</p>
					<p class="text-2xl font-bold text-gray-900 dark:text-white">
						{dash.db_available ? dash.drives_online : '--'}
					</p>
				</div>
			</div>
		</div>
	</div>

	<!-- Transcoder stats -->
	<section>
		<div class="mb-3 flex items-center gap-2">
			<div class="h-2.5 w-2.5 rounded-full {dash.transcoder_online && dash.transcoder_stats?.worker_running ? 'bg-green-500' : dash.transcoder_online ? 'bg-yellow-500' : 'bg-gray-400'}"></div>
			<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Transcoder</h2>
			<span class="text-sm text-gray-500 dark:text-gray-400">
				{#if !dashReady}
					&mdash; Loading...
				{:else if !dash.transcoder_online}
					&mdash; Offline
				{:else if dash.transcoder_stats?.worker_running}
					&mdash; Worker running
				{:else}
					&mdash; Worker idle
				{/if}
			</span>
		</div>
		<div class="grid grid-cols-2 gap-4 lg:grid-cols-5">
			<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
				<div class="flex items-center gap-2">
					<svg class="h-4 w-4 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					<p class="text-sm text-gray-500 dark:text-gray-400">Pending</p>
				</div>
				<p class="mt-1 text-3xl font-bold text-yellow-600 dark:text-yellow-400">{dash.transcoder_stats?.pending ?? 0}</p>
			</div>
			<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
				<div class="flex items-center gap-2">
					<svg class="h-4 w-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
					</svg>
					<p class="text-sm text-gray-500 dark:text-gray-400">Processing</p>
				</div>
				<p class="mt-1 text-3xl font-bold text-blue-600 dark:text-blue-400">{dash.transcoder_stats?.processing ?? 0}</p>
			</div>
			<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
				<div class="flex items-center gap-2">
					<svg class="h-4 w-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					<p class="text-sm text-gray-500 dark:text-gray-400">Completed</p>
				</div>
				<p class="mt-1 text-3xl font-bold text-green-600 dark:text-green-400">{dash.transcoder_stats?.completed ?? 0}</p>
			</div>
			<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
				<div class="flex items-center gap-2">
					<svg class="h-4 w-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					<p class="text-sm text-gray-500 dark:text-gray-400">Failed</p>
				</div>
				<p class="mt-1 text-3xl font-bold text-red-600 dark:text-red-400">{dash.transcoder_stats?.failed ?? 0}</p>
			</div>
			<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
				<div class="flex items-center gap-2">
					<svg class="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
					</svg>
					<p class="text-sm text-gray-500 dark:text-gray-400">Cancelled</p>
				</div>
				<p class="mt-1 text-3xl font-bold text-gray-600 dark:text-gray-400">{dash.transcoder_stats?.cancelled ?? 0}</p>
			</div>
		</div>
	</section>

	<!-- Disc review (waiting jobs) -->
	{#if waitingJobs.length > 0}
		<section>
			<h2 class="mb-3 text-lg font-semibold text-primary-text dark:text-primary-text-dark">New Disc Detected &mdash; Review Before Ripping</h2>
			<div class="grid gap-4">
				{#each waitingJobs as job (job.job_id)}
					<LcarsFrame variant="full" accent="#f90" label="WAITING FOR REVIEW — {(job.title || job.label || 'UNKNOWN').toUpperCase()}">
						<DiscReviewWidget {job} driveNames={dash.drive_names} paused={!dash.ripping_enabled} onrefresh={refreshDashboard} ondismiss={() => dismissJob(job.job_id)} />
					</LcarsFrame>
				{/each}
			</div>
		</section>
	{/if}

	<!-- Active rips -->
	{#if nonWaitingActiveJobs.length > 0}
		<section>
			<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Active Rips</h2>
			<LcarsFrame variant="full" accent="#99f" label="ACTIVE RIPS — {nonWaitingActiveJobs.length} IN PROGRESS">
				<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
					{#each nonWaitingActiveJobs as job (job.job_id)}
						<JobCard {job} driveNames={dash.drive_names} progress={progressMap[job.job_id]?.progress} progressStage={progressMap[job.job_id]?.stage} />
					{/each}
				</div>
			</LcarsFrame>
		</section>
	{/if}

	<!-- Active transcodes -->
	{#if dash.active_transcodes.length > 0}
		<section>
			<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Active Transcodes</h2>
			<LcarsFrame variant="full" accent="#c9c" label="TRANSCODING — {dash.active_transcodes.length} ACTIVE">
				<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
					{#each dash.active_transcodes as tc}
						<TranscodeCard job={tc} />
					{/each}
				</div>
			</LcarsFrame>
		</section>
	{/if}

	<!-- All Jobs -->
	<section class="space-y-4">
			<div class="flex flex-wrap items-center justify-between gap-4">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white">All Jobs</h2>
				<div class="flex gap-2">
					<button
						onclick={() => viewMode = 'table'}
						class="rounded-lg px-3 py-1.5 text-sm {viewMode === 'table' ? 'bg-primary text-on-primary' : 'bg-primary/15 text-gray-700 dark:bg-primary/15 dark:text-gray-300'}"
					>Table</button>
					<button
						onclick={() => viewMode = 'card'}
						class="rounded-lg px-3 py-1.5 text-sm {viewMode === 'card' ? 'bg-primary text-on-primary' : 'bg-primary/15 text-gray-700 dark:bg-primary/15 dark:text-gray-300'}"
					>Cards</button>
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
							<JobCard {job} driveNames={dash.drive_names} progress={progressMap[job.job_id]?.progress} progressStage={progressMap[job.job_id]?.stage} />
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
