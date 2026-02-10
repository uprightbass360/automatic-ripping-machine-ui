<script lang="ts">
	import { onMount } from 'svelte';
	import { createPollingStore } from '$lib/stores/polling';
	import { fetchTranscoderStats, fetchTranscoderJobs, retryTranscoderJob, deleteTranscoderJob } from '$lib/api/transcoder';
	import type { TranscoderStats, TranscoderJobListResponse } from '$lib/types/transcoder';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import ProgressBar from '$lib/components/ProgressBar.svelte';
	import TimeAgo from '$lib/components/TimeAgo.svelte';

	const emptyStats: TranscoderStats = { online: false, stats: null };
	const emptyJobs: TranscoderJobListResponse = { jobs: [], total: 0 };

	const stats = createPollingStore(fetchTranscoderStats, emptyStats, 5000);
	const statsError = stats.error;
	let activeTab = $state('all');
	let jobs = $state<TranscoderJobListResponse>(emptyJobs);
	let loadingJobs = $state(false);
	let jobsError = $state<string | null>(null);

	async function loadJobs() {
		loadingJobs = true;
		jobsError = null;
		try {
			const statusParam = activeTab === 'all' ? undefined : activeTab;
			jobs = await fetchTranscoderJobs({ status: statusParam });
		} catch (e) {
			jobsError = e instanceof Error ? e.message : 'Failed to load jobs';
			jobs = emptyJobs;
		} finally {
			loadingJobs = false;
		}
	}

	function switchTab(tab: string) {
		activeTab = tab;
		loadJobs();
	}

	async function handleRetry(id: number) {
		await retryTranscoderJob(id);
		loadJobs();
	}

	async function handleDelete(id: number) {
		if (confirm('Delete this transcode job?')) {
			await deleteTranscoderJob(id);
			loadJobs();
		}
	}

	onMount(() => {
		stats.start();
		loadJobs();
		return () => stats.stop();
	});

	const tabs = ['all', 'pending', 'processing', 'completed', 'failed'];
</script>

<svelte:head>
	<title>Transcoder - ARM UI</title>
</svelte:head>

<div class="space-y-6">
	<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Transcoder</h1>

	<!-- API error -->
	{#if $statsError}
		<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
			Failed to reach transcoder: {$statsError}
		</div>
	{/if}

	<!-- Offline banner -->
	{#if !$stats.online}
		<div class="flex items-center gap-3 rounded-lg border border-gray-300 bg-gray-50 p-4 dark:border-gray-600 dark:bg-gray-800">
			<div class="h-3 w-3 flex-shrink-0 rounded-full bg-gray-400"></div>
			<div>
				<p class="font-medium text-gray-700 dark:text-gray-300">Transcoder Offline</p>
				<p class="text-sm text-gray-500 dark:text-gray-400">The transcoder service is not responding. Transcoding features are unavailable.</p>
			</div>
		</div>
	{/if}

	<!-- Stats cards -->
	{#if $stats.online && $stats.stats}
		{@const s = $stats.stats}
		<div class="flex items-center gap-2">
			<div class="h-2.5 w-2.5 rounded-full {s.worker_running ? 'bg-green-500' : 'bg-yellow-500'}"></div>
			<span class="text-sm font-medium text-gray-700 dark:text-gray-300">
				Worker {s.worker_running ? 'running' : 'idle'}
			</span>
		</div>
		<div class="grid grid-cols-2 gap-4 lg:grid-cols-5">
			<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
				<p class="text-sm text-gray-500 dark:text-gray-400">Pending</p>
				<p class="mt-1 text-3xl font-bold text-gray-900 dark:text-white">{s.pending}</p>
			</div>
			<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
				<p class="text-sm text-gray-500 dark:text-gray-400">Processing</p>
				<p class="mt-1 text-3xl font-bold text-gray-900 dark:text-white">{s.processing}</p>
			</div>
			<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
				<p class="text-sm text-gray-500 dark:text-gray-400">Completed</p>
				<p class="mt-1 text-3xl font-bold text-gray-900 dark:text-white">{s.completed}</p>
			</div>
			<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
				<p class="text-sm text-gray-500 dark:text-gray-400">Failed</p>
				<p class="mt-1 text-3xl font-bold text-gray-900 dark:text-white">{s.failed}</p>
			</div>
			<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
				<p class="text-sm text-gray-500 dark:text-gray-400">Cancelled</p>
				<p class="mt-1 text-3xl font-bold text-gray-900 dark:text-white">{s.cancelled}</p>
			</div>
		</div>
	{/if}

	<!-- Jobs section -->
	<section class="space-y-4">
		<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Transcode Jobs</h2>

		<!-- Tabs -->
		<div class="flex gap-1 border-b border-gray-200 dark:border-gray-700">
			{#each tabs as tab}
				<button
					onclick={() => switchTab(tab)}
					class="border-b-2 px-4 py-2 text-sm font-medium capitalize transition-colors
						{activeTab === tab
							? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
							: 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
				>
					{tab}
				</button>
			{/each}
		</div>

		<!-- Jobs table -->
		{#if jobsError}
			<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
				{jobsError}
			</div>
		{:else if loadingJobs}
			<div class="py-8 text-center text-gray-400">Loading...</div>
		{:else if jobs.jobs.length === 0}
			<p class="py-8 text-center text-gray-400">No transcode jobs found.</p>
		{:else}
			<div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
				<table class="w-full text-left text-sm">
					<thead class="bg-gray-50 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
						<tr>
							<th class="px-4 py-3 font-medium">Input</th>
							<th class="px-4 py-3 font-medium">Status</th>
							<th class="px-4 py-3 font-medium">Progress</th>
							<th class="px-4 py-3 font-medium">Preset</th>
							<th class="px-4 py-3 font-medium">Started</th>
							<th class="px-4 py-3 font-medium">Actions</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
						{#each jobs.jobs as job}
							<tr class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
								<td class="max-w-[300px] truncate px-4 py-3 text-gray-900 dark:text-white" title={job.input_path}>
									{job.input_path?.split('/').pop() ?? ''}
								</td>
								<td class="px-4 py-3"><StatusBadge status={job.status} /></td>
								<td class="w-40 px-4 py-3">
									{#if typeof job.progress === 'number'}
										<ProgressBar value={job.progress} color="bg-indigo-500" />
									{:else}
										<span class="text-gray-400">&mdash;</span>
									{/if}
								</td>
								<td class="px-4 py-3 text-gray-600 dark:text-gray-400">{job.preset ?? '—'}</td>
								<td class="px-4 py-3 text-gray-600 dark:text-gray-400">
									<TimeAgo date={job.started_at ?? job.created_at} />
								</td>
								<td class="px-4 py-3">
									<div class="flex gap-2">
										{#if job.status === 'failed'}
											<button
												onclick={() => handleRetry(job.id)}
												class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700"
											>Retry</button>
										{/if}
										<button
											onclick={() => handleDelete(job.id)}
											class="rounded bg-red-600 px-2 py-1 text-xs text-white hover:bg-red-700"
										>Delete</button>
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</section>
</div>
