<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchDashboard } from '$lib/api/dashboard';
	import { fetchJobs } from '$lib/api/jobs';
	import type { DashboardData, JobListResponse } from '$lib/types/arm';
	import JobCard from '$lib/components/JobCard.svelte';
	import JobRow from '$lib/components/JobRow.svelte';
	import ProgressBar from '$lib/components/ProgressBar.svelte';
	import StatusBadge from '$lib/components/StatusBadge.svelte';

	// --- Dashboard state (simple $state, no store) ---
	let dash = $state<DashboardData>({
		db_available: true,
		active_jobs: [],
		system_info: null,
		drives_online: 0,
		notification_count: 0,
		transcoder_online: false,
		transcoder_stats: null,
		active_transcodes: []
	});
	let dashReady = $state(false);
	let dashError = $state<string | null>(null);

	async function refreshDashboard() {
		try {
			dash = await fetchDashboard();
			dashReady = true;
			dashError = null;
		} catch (e) {
			dashError = e instanceof Error ? e.message : 'Unknown error';
		}
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
		jobsLoading = true;
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
		refreshDashboard();
		loadJobs();
		const timer = setInterval(refreshDashboard, 5000);
		return () => clearInterval(timer);
	});
</script>

<svelte:head>
	<title>Dashboard - ARM UI</title>
</svelte:head>

<div class="space-y-6">
	<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>

	<!-- API error (backend unreachable) -->
	{#if dashError}
		<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
			Failed to reach backend: {dashError}
		</div>
	{/if}

	<!-- Service status banners -->
	{#if dashReady && !dash.db_available}
		<div class="flex items-center gap-3 rounded-lg border border-yellow-300 bg-yellow-50 p-4 dark:border-yellow-700 dark:bg-yellow-900/20">
			<div class="h-3 w-3 flex-shrink-0 rounded-full bg-yellow-500"></div>
			<div>
				<p class="font-medium text-yellow-800 dark:text-yellow-300">ARM Database Unavailable</p>
				<p class="text-sm text-yellow-700 dark:text-yellow-400">Cannot connect to the ARM database. Check that the database file is mounted and the path is correct.</p>
			</div>
		</div>
	{/if}

	{#if dashReady && !dash.transcoder_online}
		<div class="flex items-center gap-3 rounded-lg border border-gray-300 bg-gray-50 p-4 dark:border-gray-600 dark:bg-gray-800">
			<div class="h-3 w-3 flex-shrink-0 rounded-full bg-gray-400"></div>
			<div>
				<p class="font-medium text-gray-700 dark:text-gray-300">Transcoder Offline</p>
				<p class="text-sm text-gray-500 dark:text-gray-400">The transcoder service is not responding. Transcoding features are unavailable.</p>
			</div>
		</div>
	{/if}

	<!-- Stats cards -->
	<div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
		<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
			<p class="text-sm text-gray-500 dark:text-gray-400">Active Rips</p>
			<p class="mt-1 text-3xl font-bold text-gray-900 dark:text-white">
				{dash.db_available ? dash.active_jobs.length : '--'}
			</p>
		</div>
		<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
			<p class="text-sm text-gray-500 dark:text-gray-400">Active Transcodes</p>
			<p class="mt-1 text-3xl font-bold text-gray-900 dark:text-white">
				{dashReady ? (dash.transcoder_online ? dash.active_transcodes.length : '--') : '...'}
			</p>
		</div>
		<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
			<p class="text-sm text-gray-500 dark:text-gray-400">Drives Online</p>
			<p class="mt-1 text-3xl font-bold text-gray-900 dark:text-white">
				{dash.db_available ? dash.drives_online : '--'}
			</p>
		</div>
		<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
			<p class="text-sm text-gray-500 dark:text-gray-400">System</p>
			<div class="mt-1">
				{#if dash.system_info}
					<p class="text-sm text-gray-700 dark:text-gray-300">CPU: {dash.system_info.cpu ?? 'N/A'}</p>
					<p class="text-sm text-gray-700 dark:text-gray-300">RAM: {dash.system_info.mem_total ? `${dash.system_info.mem_total.toFixed(1)} GB` : 'N/A'}</p>
				{:else}
					<p class="text-sm text-gray-400">{dash.db_available ? 'No data' : '--'}</p>
				{/if}
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
			<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
				<p class="text-sm text-gray-500 dark:text-gray-400">Pending</p>
				<p class="mt-1 text-3xl font-bold text-gray-900 dark:text-white">{dash.transcoder_stats?.pending ?? 0}</p>
			</div>
			<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
				<p class="text-sm text-gray-500 dark:text-gray-400">Processing</p>
				<p class="mt-1 text-3xl font-bold text-gray-900 dark:text-white">{dash.transcoder_stats?.processing ?? 0}</p>
			</div>
			<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
				<p class="text-sm text-gray-500 dark:text-gray-400">Completed</p>
				<p class="mt-1 text-3xl font-bold text-gray-900 dark:text-white">{dash.transcoder_stats?.completed ?? 0}</p>
			</div>
			<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
				<p class="text-sm text-gray-500 dark:text-gray-400">Failed</p>
				<p class="mt-1 text-3xl font-bold text-gray-900 dark:text-white">{dash.transcoder_stats?.failed ?? 0}</p>
			</div>
			<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
				<p class="text-sm text-gray-500 dark:text-gray-400">Cancelled</p>
				<p class="mt-1 text-3xl font-bold text-gray-900 dark:text-white">{dash.transcoder_stats?.cancelled ?? 0}</p>
			</div>
		</div>
	</section>

	<!-- Active rips -->
	{#if dash.active_jobs.length > 0}
		<section>
			<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Active Rips</h2>
			<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
				{#each dash.active_jobs as job (job.job_id)}
					<JobCard {job} />
				{/each}
			</div>
		</section>
	{/if}

	<!-- Active transcodes -->
	{#if dash.active_transcodes.length > 0}
		<section>
			<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Active Transcodes</h2>
			<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
				{#each dash.active_transcodes as tc}
					<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
						<div class="flex items-start justify-between gap-2">
							<p class="truncate font-medium text-gray-900 dark:text-white">
								{tc.title || tc.source_path?.split('/').pop() || `Transcode #${tc.id}`}
							</p>
							<StatusBadge status={tc.status} />
						</div>
						{#if typeof tc.progress === 'number'}
							<div class="mt-3">
								<ProgressBar value={tc.progress} color="bg-indigo-500" />
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</section>
	{/if}

	<!-- All Jobs -->
	<section class="space-y-4">
			<div class="flex flex-wrap items-center justify-between gap-4">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white">All Jobs</h2>
				<div class="flex gap-2">
					<button
						onclick={() => viewMode = 'table'}
						class="rounded-lg px-3 py-1.5 text-sm {viewMode === 'table' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'}"
					>Table</button>
					<button
						onclick={() => viewMode = 'card'}
						class="rounded-lg px-3 py-1.5 text-sm {viewMode === 'card' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'}"
					>Cards</button>
				</div>
			</div>

			<!-- Filters -->
			<div class="flex flex-wrap gap-3">
				<input
					type="text"
					placeholder="Search titles..."
					oninput={onSearch}
					class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-white"
				/>
				<select
					value={statusFilter}
					onchange={(e) => setFilter('status', (e.target as HTMLSelectElement).value)}
					class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-white"
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
					class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-white"
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
					<div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
						<table class="w-full text-left text-sm">
							<thead class="bg-gray-50 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
								<tr>
									<th class="px-4 py-3 font-medium">Title</th>
									<th class="px-4 py-3 font-medium">Year</th>
									<th class="px-4 py-3 font-medium">Status</th>
									<th class="px-4 py-3 font-medium">Type</th>
									<th class="px-4 py-3 font-medium">Disc</th>
									<th class="px-4 py-3 font-medium">Device</th>
									<th class="px-4 py-3 font-medium">Started</th>
									<th class="px-4 py-3 font-medium">Actions</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
								{#each jobsData.jobs as job (job.job_id)}
									<JobRow {job} onaction={loadJobs} />
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
						{#each jobsData.jobs as job (job.job_id)}
							<JobCard {job} />
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
								class="rounded px-3 py-1 text-sm disabled:opacity-50 bg-gray-200 dark:bg-gray-700 dark:text-gray-300"
							>Prev</button>
							{#each Array.from({ length: jobsData.pages }, (_, i) => i + 1) as p}
								{#if p === jobsData.page || p === 1 || p === jobsData.pages || Math.abs(p - jobsData.page) <= 1}
									<button
										onclick={() => goPage(p)}
										class="rounded px-3 py-1 text-sm {p === jobsData.page ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-700 dark:text-gray-300'}"
									>{p}</button>
								{:else if Math.abs(p - jobsData.page) === 2}
									<span class="px-1 text-gray-400">...</span>
								{/if}
							{/each}
							<button
								disabled={jobsData.page >= jobsData.pages}
								onclick={() => goPage(jobsData!.page + 1)}
								class="rounded px-3 py-1 text-sm disabled:opacity-50 bg-gray-200 dark:bg-gray-700 dark:text-gray-300"
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
