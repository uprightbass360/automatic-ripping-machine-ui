<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchJobs } from '$lib/api/jobs';
	import type { Job, JobListResponse } from '$lib/types/arm';
	import JobRow from '$lib/components/JobRow.svelte';

	let data = $state<JobListResponse | null>(null);
	let error = $state<string | null>(null);
	let loading = $state(true);

	let page = $state(1);
	let perPage = $state(25);
	let statusFilter = $state('');
	let videoTypeFilter = $state('');
	let searchQuery = $state('');
	let searchTimeout: ReturnType<typeof setTimeout>;

	async function load() {
		if (!data) loading = true;
		error = null;
		try {
			data = await fetchJobs({
				page,
				per_page: perPage,
				status: statusFilter || undefined,
				search: searchQuery || undefined,
				video_type: videoTypeFilter || undefined
			});
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load jobs';
		} finally {
			loading = false;
		}
	}

	function onSearch(e: Event) {
		const val = (e.target as HTMLInputElement).value;
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			searchQuery = val;
			page = 1;
			load();
		}, 300);
	}

	function setFilter(type: 'status' | 'videoType', value: string) {
		if (type === 'status') statusFilter = value;
		else videoTypeFilter = value;
		page = 1;
		load();
	}

	function goPage(p: number) {
		page = p;
		load();
	}

	onMount(() => {
		load();
	});
</script>

<svelte:head>
	<title>ARM - Jobs</title>
</svelte:head>

<div class="space-y-4">
	<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Jobs</h1>

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
			<option value="data">Data</option>
		</select>
	</div>

	{#if error}
		<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
			{error}
		</div>
	{:else if loading}
		<div class="py-8 text-center text-gray-400">Loading...</div>
	{:else if data}
		<div class="overflow-x-auto rounded-lg border border-primary/20 dark:border-primary/20">
			<table class="w-full text-left text-sm">
				<thead class="bg-page text-gray-600 dark:bg-primary/5 dark:text-gray-400">
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
					{#each data.jobs as job (job.job_id)}
						<JobRow {job} onaction={load} />
					{/each}
				</tbody>
			</table>
		</div>

		<!-- Pagination -->
		{#if data.pages > 1}
			<div class="flex items-center justify-between">
				<p class="text-sm text-gray-500 dark:text-gray-400">
					Showing {(data.page - 1) * data.per_page + 1}–{Math.min(data.page * data.per_page, data.total)} of {data.total}
				</p>
				<div class="flex gap-1">
					<button
						disabled={data.page <= 1}
						onclick={() => goPage(data!.page - 1)}
						class="rounded-sm px-3 py-1 text-sm disabled:opacity-50 bg-primary/15 dark:bg-primary/15 dark:text-gray-300"
					>Prev</button>
					{#each Array.from({ length: data.pages }, (_, i) => i + 1) as p}
						{#if p === data.page || p === 1 || p === data.pages || Math.abs(p - data.page) <= 1}
							<button
								onclick={() => goPage(p)}
								class="rounded-sm px-3 py-1 text-sm {p === data.page ? 'bg-primary text-on-primary' : 'bg-primary/15 dark:bg-primary/15 dark:text-gray-300'}"
							>{p}</button>
						{:else if Math.abs(p - data.page) === 2}
							<span class="px-1 text-gray-400">...</span>
						{/if}
					{/each}
					<button
						disabled={data.page >= data.pages}
						onclick={() => goPage(data!.page + 1)}
						class="rounded-sm px-3 py-1 text-sm disabled:opacity-50 bg-primary/15 dark:bg-primary/15 dark:text-gray-300"
					>Next</button>
				</div>
			</div>
		{/if}

		{#if data.jobs.length === 0}
			<p class="py-8 text-center text-gray-400">No jobs found.</p>
		{/if}
	{/if}
</div>
