<script lang="ts">
	import { onMount } from 'svelte';
	import { createPollingStore } from '$lib/stores/polling';
	import { fetchTranscoderStats, fetchTranscoderJobs, retryTranscoderJob, deleteTranscoderJob, retranscodeTranscoderJob } from '$lib/api/transcoder';
	import { fetchStructuredTranscoderLogContent } from '$lib/api/logs';
	import type { TranscoderStats, TranscoderJobListResponse } from '$lib/types/transcoder';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import ProgressBar from '$lib/components/ProgressBar.svelte';
	import TimeAgo from '$lib/components/TimeAgo.svelte';
	import InlineLogFeed from '$lib/components/InlineLogFeed.svelte';

	const emptyStats: TranscoderStats = { online: false, stats: null };
	const emptyJobs: TranscoderJobListResponse = { jobs: [], total: 0 };

	const stats = createPollingStore(fetchTranscoderStats, emptyStats, 5000);
	const statsError = stats.error;
	let activeTab = $state('all');
	let jobs = $state<TranscoderJobListResponse>(emptyJobs);
	let loadingJobs = $state(false);
	let jobsError = $state<string | null>(null);

	function formatDuration(startISO: string | null, endISO?: string | null): string | null {
		if (!startISO) return null;
		const start = new Date(startISO).getTime();
		if (isNaN(start)) return null;
		const end = endISO ? new Date(endISO).getTime() : Date.now();
		if (isNaN(end)) return null;
		const diffSec = Math.max(0, Math.floor((end - start) / 1000));
		const h = Math.floor(diffSec / 3600);
		const m = Math.floor((diffSec % 3600) / 60);
		const s = diffSec % 60;
		if (h > 0) return `${h}h ${m}m ${s}s`;
		if (m > 0) return `${m}m ${s}s`;
		return `${s}s`;
	}

	function sourceBasename(path: string | null | undefined): string {
		if (!path) return '';
		const parts = path.replace(/\/+$/, '').split('/');
		return parts[parts.length - 1] ?? '';
	}

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

	async function handleRetranscode(id: number) {
		await retranscodeTranscoderJob(id);
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
	<title>ARM - Transcoder</title>
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
		<div class="flex items-center gap-3 rounded-lg border border-primary/25 bg-page p-4 dark:border-primary/25 dark:bg-page-dark">
			<div class="h-3 w-3 shrink-0 rounded-full bg-gray-400"></div>
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
				Worker {s.worker_running ? 'running' : 'idle'}{#if s.worker_running && s.current_job}
					<span class="text-gray-500 dark:text-gray-400"> &mdash; {s.current_job}</span>
				{/if}
			</span>
		</div>
		<div class="grid grid-cols-2 gap-4 lg:grid-cols-5">
			<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
				<p class="text-sm text-gray-500 dark:text-gray-400">Pending</p>
				<p class="mt-1 text-3xl font-bold text-primary-text dark:text-primary-text-dark">{s.pending}</p>
			</div>
			<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
				<p class="text-sm text-gray-500 dark:text-gray-400">Processing</p>
				<p class="mt-1 text-3xl font-bold text-indigo-600 dark:text-indigo-400">{s.processing}</p>
			</div>
			<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
				<p class="text-sm text-gray-500 dark:text-gray-400">Completed</p>
				<p class="mt-1 text-3xl font-bold text-green-600 dark:text-green-400">{s.completed}</p>
			</div>
			<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
				<p class="text-sm text-gray-500 dark:text-gray-400">Failed</p>
				<p class="mt-1 text-3xl font-bold text-red-600 dark:text-red-400">{s.failed}</p>
			</div>
			<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
				<p class="text-sm text-gray-500 dark:text-gray-400">Cancelled</p>
				<p class="mt-1 text-3xl font-bold text-gray-500 dark:text-gray-400">{s.cancelled}</p>
			</div>
		</div>
	{/if}

	<!-- Jobs section -->
	<section class="space-y-4">
		<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Transcode Jobs</h2>

		<!-- Tabs -->
		<div class="flex gap-1 border-b border-primary/20 dark:border-primary/20">
			{#each tabs as tab}
				<button
					onclick={() => switchTab(tab)}
					class="border-b-2 px-4 py-2 text-sm font-medium capitalize transition-colors
						{activeTab === tab
							? 'border-primary text-primary-text dark:border-primary-text-dark dark:text-primary-text-dark'
							: 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
				>
					{tab}
				</button>
			{/each}
		</div>

		<!-- Jobs list -->
		{#if jobsError}
			<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
				{jobsError}
			</div>
		{:else if loadingJobs}
			<div class="py-8 text-center text-gray-400">Loading...</div>
		{:else if jobs.jobs.length === 0}
			<p class="py-8 text-center text-gray-400">No transcode jobs found.</p>
		{:else}
			<div class="space-y-3">
				{#each jobs.jobs as job}
					<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
						<!-- Top row: title, status, actions -->
						<div class="flex items-start justify-between gap-4">
							<div class="min-w-0 flex-1">
								<div class="flex items-center gap-3">
									<h3 class="truncate font-semibold text-gray-900 dark:text-white" title={job.title}>
										{job.title || 'Untitled'}
									</h3>
									<StatusBadge status={job.status} />
								</div>
								{#if job.source_path}
									<p class="mt-1 truncate font-mono text-xs text-gray-500 dark:text-gray-400" title={job.source_path}>
										{sourceBasename(job.source_path)}
									</p>
								{/if}
							</div>
							<div class="flex shrink-0 gap-2">
								{#if job.status === 'completed' || job.status === 'failed'}
									<button
										onclick={() => handleRetranscode(job.id)}
										class="rounded-sm bg-indigo-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-indigo-700"
									>Re-transcode</button>
								{/if}
								{#if job.status === 'failed'}
									<button
										onclick={() => handleRetry(job.id)}
										class="rounded-sm bg-primary px-2.5 py-1 text-xs font-medium text-on-primary hover:bg-primary-hover"
									>Retry</button>
								{/if}
								<button
									onclick={() => handleDelete(job.id)}
									class="rounded-sm bg-red-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-red-700"
								>Delete</button>
							</div>
						</div>

						<!-- Error message for failed jobs -->
						{#if job.status === 'failed' && job.error}
							<p class="mt-2 rounded-sm bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
								{job.error}
							</p>
						{/if}

						<!-- Progress bar for pending/processing -->
						{#if (job.status === 'pending' || job.status === 'processing') && typeof job.progress === 'number'}
							<div class="mt-3">
								<ProgressBar value={job.progress} color="bg-indigo-500" />
							</div>
						{/if}

						<!-- Bottom row: timestamps + duration -->
						<div class="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500 dark:text-gray-400">
							{#if job.created_at}
								<span>Queued <TimeAgo date={job.created_at} /></span>
							{/if}
							{#if job.started_at}
								<span>Started <TimeAgo date={job.started_at} /></span>
							{/if}
							{#if job.status === 'completed' && job.started_at}
								{@const dur = formatDuration(job.started_at, job.completed_at)}
								{#if dur}
									<span class="text-green-600 dark:text-green-400">Took {dur}</span>
								{/if}
							{:else if job.status === 'processing' && job.started_at}
								{@const dur = formatDuration(job.started_at)}
								{#if dur}
									<span class="text-indigo-600 dark:text-indigo-400">Running for {dur}</span>
								{/if}
							{/if}
						</div>

						<!-- Per-job log preview -->
						{#if job.logfile}
							<InlineLogFeed
								logfile={job.logfile}
								maxEntries={8}
								fetchFn={fetchStructuredTranscoderLogContent}
								logLinkBase="/logs/transcoder"
								autoRefresh={job.status === 'processing'}
								containerClass="mt-3"
							/>
						{/if}
					</div>
				{/each}
			</div>
		{/if}
	</section>
</div>
