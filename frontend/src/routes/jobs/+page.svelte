<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchJobs, fetchJobStats, bulkDeleteJobs, bulkPurgeJobs, type JobStats } from '$lib/api/jobs';
	import type { Job, JobListResponse } from '$lib/types/arm';
	import JobRow from '$lib/components/JobRow.svelte';

	// Data
	let data = $state<JobListResponse | null>(null);
	let stats = $state<JobStats | null>(null);
	let error = $state<string | null>(null);
	let loading = $state(true);

	// Pagination
	let page = $state(1);
	let perPage = $state(25);

	// Filters
	let statusFilter = $state('');
	let videoTypeFilter = $state('');
	let disctypeFilter = $state('');
	let daysFilter = $state<number | undefined>(undefined);
	let searchQuery = $state('');
	let searchTimeout: ReturnType<typeof setTimeout>;

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
		data !== null && data.jobs.length > 0 && data.jobs.every((j) => selectedJobs.has(j.job_id))
	);

	function filterParams() {
		return {
			search: searchQuery || undefined,
			video_type: videoTypeFilter || undefined,
			disctype: disctypeFilter || undefined,
			days: daysFilter
		};
	}

	async function load() {
		if (!data) loading = true;
		error = null;
		selectedJobs = new Set();
		try {
			const fp = filterParams();
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
			data = jobsResult;
			stats = statsResult;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load jobs';
		} finally {
			loading = false;
		}
	}

	async function loadStats() {
		try {
			stats = await fetchJobStats(filterParams());
		} catch {
			// silent — stats are supplementary
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

	function setStatusFilter(value: string) {
		statusFilter = value;
		page = 1;
		load();
	}

	function setVideoTypeFilter(value: string) {
		videoTypeFilter = value;
		page = 1;
		load();
	}

	function setDisctypeFilter(value: string) {
		disctypeFilter = value;
		page = 1;
		load();
	}

	function setDaysFilter(value: number | undefined) {
		daysFilter = value;
		page = 1;
		load();
	}

	function toggleSort(col: string) {
		if (sortBy === col) {
			sortDir = sortDir === 'desc' ? 'asc' : 'desc';
		} else {
			sortBy = col;
			sortDir = 'desc';
		}
		load();
	}

	function sortIcon(col: string): string {
		if (sortBy !== col) return '↕';
		return sortDir === 'desc' ? '▼' : '▲';
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
		if (!data) return;
		if (allVisibleSelected) {
			selectedJobs = new Set();
		} else {
			selectedJobs = new Set(data.jobs.map((j) => j.job_id));
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
			await load();
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
		load();
	}

	onMount(() => {
		load();
	});

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
</script>

<svelte:head>
	<title>ARM - Jobs</title>
</svelte:head>

<!-- Close gear menu on click outside -->
<svelte:window onclick={() => (gearOpen = false)} />

<div class="space-y-4">
	<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Jobs</h1>

	<!-- Stats Bar -->
	{#if stats}
		<div class="flex flex-wrap gap-3">
			{#each statsCards as card}
				<button
					onclick={() => setStatusFilter(card.filter)}
					class="flex min-w-[120px] flex-1 cursor-pointer items-center gap-3 rounded-lg border-l-4 {card.border} {card.bg} px-4 py-3 transition-shadow hover:shadow-md {statusFilter === card.filter ? 'ring-2 ring-primary/40' : ''}"
				>
					<div>
						<div class="text-2xl font-bold {card.text}">{stats[card.key]}</div>
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
						onclick={() => handleBulkAction('delete', { status: 'fail' }, `delete all failed jobs${stats?.fail ? ` (${stats.fail})` : ''}`)}
						class="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-primary/5 dark:text-gray-300 dark:hover:bg-primary/10"
					>Delete All Failed{#if stats?.fail} ({stats.fail}){/if}</button>
					<button
						onclick={() => handleBulkAction('purge', { status: 'fail' }, `purge all failed jobs and their files`)}
						class="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
					>Purge All Failed</button>
					<button
						onclick={() => handleBulkAction('delete', { status: 'success' }, `delete all successful jobs${stats?.success ? ` (${stats.success})` : ''}`)}
						class="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-primary/5 dark:text-gray-300 dark:hover:bg-primary/10"
					>Delete All Successful{#if stats?.success} ({stats.success}){/if}</button>
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

	<!-- Error -->
	{#if error}
		<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
			{error}
		</div>
	{:else if loading}
		<div class="py-8 text-center text-gray-400">Loading...</div>
	{:else if data}
		<!-- Table -->
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
					{#each data.jobs as job (job.job_id)}
						<JobRow
							{job}
							onaction={load}
							selected={selectedJobs.has(job.job_id)}
							onselect={toggleSelect}
						/>
					{/each}
				</tbody>
			</table>
		</div>

		<!-- Pagination -->
		{#if data.pages > 1}
			<div class="flex items-center justify-between">
				<p class="text-sm text-gray-500 dark:text-gray-400">
					Showing {(data.page - 1) * data.per_page + 1}&ndash;{Math.min(data.page * data.per_page, data.total)} of {data.total}
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
