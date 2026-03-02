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

	function overallProgress(p: RipProgress | undefined): number | null {
		if (!p || p.progress == null) return null;
		if (p.tracks_total > 0) {
			if (p.tracks_ripped >= p.tracks_total) return 100;
			return ((p.tracks_ripped + p.progress / 100) / p.tracks_total) * 100;
		}
		// No tracks in DB yet (scan/decrypt phase) — show indeterminate bar.
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

	<!-- Unified status bar: services + activity + queue -->
	{#if dashReady}
		<div class="rounded-lg border border-primary/20 bg-surface dark:bg-surface-dark">
			<!-- Top row: service health (left) + activity counters (right) -->
			<div class="flex flex-wrap items-center justify-between gap-x-6 gap-y-3 px-4 py-3">
				<div class="flex items-center gap-5">
					<div class="flex items-center gap-2">
						<div class="h-2 w-2 shrink-0 rounded-full {dash.arm_online ? 'bg-green-500' : 'bg-red-500'}"></div>
						<span class="text-sm text-gray-600 dark:text-gray-400">ARM</span>
						<span class="text-sm font-medium {dash.arm_online ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
							{dash.arm_online ? 'Online' : 'Unreachable'}
						</span>
					</div>
					<div class="flex items-center gap-2">
						<div class="h-2 w-2 shrink-0 rounded-full {dash.db_available ? 'bg-green-500' : 'bg-yellow-500'}"></div>
						<span class="text-sm text-gray-600 dark:text-gray-400">Database</span>
						<span class="text-sm font-medium {dash.db_available ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'}">
							{dash.db_available ? 'Connected' : 'Unavailable'}
						</span>
					</div>
					<div class="flex items-center gap-2">
						<div class="h-2 w-2 shrink-0 rounded-full {dash.transcoder_online && dash.transcoder_stats?.worker_running ? 'bg-green-500' : dash.transcoder_online ? 'bg-yellow-500' : 'bg-gray-400'}"></div>
						<span class="text-sm text-gray-600 dark:text-gray-400">Transcoder</span>
						<span class="text-sm font-medium {dash.transcoder_online && dash.transcoder_stats?.worker_running ? 'text-green-600 dark:text-green-400' : dash.transcoder_online ? 'text-yellow-600 dark:text-yellow-400' : 'text-gray-500 dark:text-gray-400'}">
							{#if dash.transcoder_online && dash.transcoder_stats?.worker_running}Running{:else if dash.transcoder_online}Idle{:else}Offline{/if}
						</span>
					</div>
				</div>
				<div class="flex items-center gap-5 text-sm">
					<div class="flex items-center gap-1.5">
						<span class="text-lg font-bold text-gray-900 dark:text-white">{dash.db_available ? dash.active_jobs.length : '--'}</span>
						<span class="text-gray-500 dark:text-gray-400">Rips</span>
					</div>
					<div class="flex items-center gap-1.5">
						<span class="text-lg font-bold text-gray-900 dark:text-white">{dash.transcoder_online ? dash.active_transcodes.length : '--'}</span>
						<span class="text-gray-500 dark:text-gray-400">Transcodes</span>
					</div>
					<div class="flex items-center gap-1.5">
						<span class="text-lg font-bold text-gray-900 dark:text-white">{dash.db_available ? dash.drives_online : '--'}</span>
						<span class="text-gray-500 dark:text-gray-400">Drives</span>
					</div>
				</div>
			</div>
			<!-- Bottom row: transcoder queue breakdown -->
			{#if dash.transcoder_online}
				<div class="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-primary/10 px-4 py-2">
					<span class="text-xs font-medium uppercase tracking-wide text-gray-400 dark:text-gray-500">Queue</span>
					<span class="text-sm"><span class="font-semibold text-yellow-600 dark:text-yellow-400">{dash.transcoder_stats?.pending ?? 0}</span> <span class="text-gray-500 dark:text-gray-400">pending</span></span>
					<span class="text-gray-300 dark:text-gray-600">&middot;</span>
					<span class="text-sm"><span class="font-semibold text-blue-600 dark:text-blue-400">{dash.transcoder_stats?.processing ?? 0}</span> <span class="text-gray-500 dark:text-gray-400">processing</span></span>
					<span class="text-gray-300 dark:text-gray-600">&middot;</span>
					<span class="text-sm"><span class="font-semibold text-green-600 dark:text-green-400">{dash.transcoder_stats?.completed ?? 0}</span> <span class="text-gray-500 dark:text-gray-400">completed</span></span>
					<span class="text-gray-300 dark:text-gray-600">&middot;</span>
					<span class="text-sm"><span class="font-semibold text-red-600 dark:text-red-400">{dash.transcoder_stats?.failed ?? 0}</span> <span class="text-gray-500 dark:text-gray-400">failed</span></span>
					<span class="text-gray-300 dark:text-gray-600">&middot;</span>
					<span class="text-sm"><span class="font-semibold text-gray-600 dark:text-gray-400">{dash.transcoder_stats?.cancelled ?? 0}</span> <span class="text-gray-500 dark:text-gray-400">cancelled</span></span>
				</div>
			{/if}
		</div>
	{/if}

	<!-- Disc review (waiting jobs) -->
	{#if waitingJobs.length > 0}
		<section>
			<div class="grid gap-4">
				{#each waitingJobs as job (job.job_id)}
					<DiscReviewWidget {job} driveNames={dash.drive_names} paused={!dash.ripping_enabled} onrefresh={refreshDashboard} ondismiss={() => dismissJob(job.job_id)} />
				{/each}
			</div>
		</section>
	{/if}

	<!-- Active rips -->
	{#if nonWaitingActiveJobs.length > 0}
		<section>
			<LcarsFrame variant="full" accent="#99f" label="ACTIVE RIPS — {nonWaitingActiveJobs.length} IN PROGRESS">
				<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
					{#each nonWaitingActiveJobs as job (job.job_id)}
						<JobCard {job} driveNames={dash.drive_names} progress={overallProgress(progressMap[job.job_id])} progressStage={progressMap[job.job_id]?.stage} />
					{/each}
				</div>
			</LcarsFrame>
		</section>
	{/if}

	<!-- Active transcodes -->
	{#if dash.active_transcodes.length > 0}
		<section>
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
