<script lang="ts">
	import { onMount } from 'svelte';
	import { createPollingStore } from '$lib/stores/polling';
	import { fetchTranscoderStats, fetchTranscoderJobs, retryTranscoderJob, deleteTranscoderJob, retranscodeTranscoderJob } from '$lib/api/transcoder';
	import { fetchStructuredTranscoderLogContent } from '$lib/api/logs';
	import type { TranscoderStats, TranscoderJobListResponse } from '$lib/types/transcoder';
	import { getVideoTypeConfig, discTypeLabel } from '$lib/utils/job-type';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import DiscTypeIcon from '$lib/components/DiscTypeIcon.svelte';
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
					{@const typeConfig = getVideoTypeConfig(job.video_type)}
					<div class="rounded-lg border border-primary/20 border-l-4 {typeConfig.accentBorder} bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
						<div class="flex gap-4">
							<!-- Poster -->
							{#if job.poster_url}
								<img
									src={job.poster_url}
									alt={job.title ?? 'Poster'}
									class="h-24 w-16 shrink-0 rounded-sm object-cover"
								/>
							{:else}
								<div class="flex h-24 w-16 shrink-0 items-center justify-center rounded-sm {typeConfig.placeholderClasses}">
									<svg class="h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
										<circle cx="12" cy="12" r="10" />
										<circle cx="12" cy="12" r="3" />
										<circle cx="12" cy="12" r="6.5" stroke-width="0.75" opacity="0.4" />
									</svg>
								</div>
							{/if}

							<div class="min-w-0 flex-1">
								<!-- Row 1: Title + Status + Actions -->
								<div class="flex items-start justify-between gap-2">
									<div class="flex min-w-0 items-center gap-3">
										<h3 class="truncate font-semibold text-gray-900 dark:text-white" title={job.title}>
											{job.title || 'Untitled'}
										</h3>
										<StatusBadge status={job.status} />
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

								<!-- Row 2: Year, ARM link, source basename -->
								<div class="mt-0.5 flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
									{#if job.year}
										<span>{job.year}</span>
									{/if}
									{#if job.arm_job_id}
										<a
											href="/jobs/{job.arm_job_id}"
											class="inline-flex items-center rounded-sm bg-primary/10 px-1.5 py-0.5 text-xs font-medium text-primary-text hover:bg-primary/20 dark:bg-primary/15 dark:text-primary-text-dark dark:hover:bg-primary/25"
										>ARM #{job.arm_job_id}</a>
									{/if}
									{#if job.source_path}
										<span class="truncate font-mono text-xs text-gray-400 dark:text-gray-500" title={job.source_path}>{sourceBasename(job.source_path)}</span>
									{/if}
								</div>

								<!-- Row 3: Type badge, disc type, tracks -->
								<div class="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-xs text-gray-500 dark:text-gray-400">
									<span class="rounded-sm px-1.5 py-0.5 font-medium {typeConfig.badgeClasses}">{typeConfig.label}</span>
									{#if job.disctype}
										<span class="inline-flex items-center gap-1 rounded-sm bg-primary/10 px-1.5 py-0.5 dark:bg-primary/15">
											<DiscTypeIcon disctype={job.disctype} size="h-3.5 w-3.5" />
											{discTypeLabel(job.disctype)}
										</span>
									{/if}
									{#if job.total_tracks != null && job.total_tracks > 0}
										<span>{job.total_tracks} track{job.total_tracks === 1 ? '' : 's'}</span>
									{/if}
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

								<!-- Timestamps + duration -->
								<div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500 dark:text-gray-400">
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

								<!-- Output path for completed jobs -->
								{#if job.status === 'completed' && job.output_path}
									<p class="mt-2 flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
										<span class="text-gray-400 dark:text-gray-500">&rarr;</span>
										<span class="truncate font-mono" title={job.output_path}>{sourceBasename(job.output_path)}</span>
									</p>
								{/if}
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</section>
</div>
