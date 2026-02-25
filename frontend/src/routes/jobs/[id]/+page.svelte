<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { fetchJob, retranscodeJob } from '$lib/api/jobs';
	import type { JobDetail } from '$lib/types/arm';
	import JobActions from '$lib/components/JobActions.svelte';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import TitleSearch from '$lib/components/TitleSearch.svelte';
	import RipSettings from '$lib/components/RipSettings.svelte';
	import { formatDateTime, timeAgo } from '$lib/utils/format';
	import { discTypeLabel, isJobActive } from '$lib/utils/job-type';

	let job = $state<JobDetail | null>(null);
	let error = $state<string | null>(null);
	let showTitleSearch = $state(false);
	let showRipSettings = $state(false);
	let retranscoding = $state(false);
	let retranscodeFeedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);

	async function handleRetranscode() {
		if (!job) return;
		retranscoding = true;
		retranscodeFeedback = null;
		try {
			const result = await retranscodeJob(job.job_id);
			retranscodeFeedback = { type: 'success', message: result.message || 'Queued for transcoding' };
		} catch (e) {
			retranscodeFeedback = { type: 'error', message: e instanceof Error ? e.message : 'Failed to queue' };
		} finally {
			retranscoding = false;
		}
	}

	let isVideoDisc = $derived(
		job?.disctype === 'dvd' || job?.disctype === 'bluray' || job?.disctype === 'bluray4k'
	);

	let isMusicDisc = $derived(
		job?.disctype === 'music' || job?.video_type === 'music'
	);

	let hasAutoManualDiff = $derived(
		job != null &&
			job.title_auto != null &&
			job.title != null &&
			job.title_auto !== job.title
	);

	async function loadJob() {
		const id = Number($page.params.id);
		try {
			job = await fetchJob(id);
		} catch (e) {
			if (e instanceof Error && e.message.includes('404')) {
				goto('/jobs');
				return;
			}
			error = e instanceof Error ? e.message : 'Failed to load job';
		}
	}

	function handleTitleApply() {
		showTitleSearch = false;
		loadJob();
	}

	function handleConfigSaved() {
		showRipSettings = false;
		loadJob();
	}

	onMount(() => {
		let stopped = false;
		async function poll() {
			while (!stopped) {
				await new Promise((r) => setTimeout(r, 5000));
				if (job && isJobActive(job.status)) {
					await loadJob();
				} else {
					break;
				}
			}
		}
		loadJob().then(poll);
		return () => {
			stopped = true;
		};
	});
</script>

<svelte:head>
	<title>ARM - {job?.title || 'Job Detail'}</title>
</svelte:head>

{#if error}
	<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
		{error}
	</div>
{:else if !job}
	<div class="py-8 text-center text-gray-400">Loading...</div>
{:else}
	<div class="space-y-6">
		<!-- Back link -->
		<a href="/jobs" class="inline-flex items-center gap-1 text-sm text-primary-text hover:underline dark:text-primary-text-dark">
			<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
			</svg>
			Back to Jobs
		</a>

		<!-- Header -->
		<div class="flex flex-col gap-6 md:flex-row">
			{#if job.poster_url}
				<img
					src={job.poster_url}
					alt={job.title ?? 'Poster'}
					class="h-64 w-44 rounded-lg object-cover shadow-md"
				/>
			{/if}
			<div class="flex-1 space-y-3">
				<div class="flex flex-wrap items-center gap-3">
					<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
						{job.title || job.label || 'Untitled'}
					</h1>
					{#if job.year}
						<span class="text-lg text-gray-500 dark:text-gray-400">({job.year})</span>
					{/if}
					<StatusBadge status={job.status} />
				</div>

				<JobActions {job} onaction={loadJob} />

				{#if isVideoDisc && (job.status === 'success' || job.status === 'fail')}
					<div class="flex items-center gap-3">
						<button
							onclick={handleRetranscode}
							disabled={retranscoding}
							class="rounded-lg px-3 py-1.5 text-sm font-medium bg-indigo-100 text-indigo-700 hover:bg-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 dark:hover:bg-indigo-900/50 disabled:opacity-50 transition-colors"
						>
							{retranscoding ? 'Queuing...' : 'Re-transcode'}
						</button>
						{#if retranscodeFeedback}
							<span class="text-sm {retranscodeFeedback.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
								{retranscodeFeedback.message}
							</span>
						{/if}
					</div>
				{/if}

				{#if job.imdb_id && !isMusicDisc}
					<a
						href="https://www.imdb.com/title/{job.imdb_id}"
						target="_blank"
						rel="noopener noreferrer"
						class="inline-flex items-center gap-1 rounded bg-yellow-400 px-2 py-0.5 text-xs font-bold text-black"
					>
						IMDb
					</a>
				{/if}

				<dl class="grid grid-cols-2 gap-x-6 gap-y-2 text-sm md:grid-cols-3">
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Status</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{job.status ?? 'N/A'}</dd>
					</div>
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Stage</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{job.stage ?? 'N/A'}</dd>
					</div>
					{#if !isMusicDisc}
						<div>
							<dt class="text-gray-500 dark:text-gray-400">Video Type</dt>
							<dd class="font-medium text-gray-900 dark:text-white">{job.video_type ?? 'N/A'}</dd>
						</div>
					{/if}
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Disc Type</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{discTypeLabel(job.disctype)}</dd>
					</div>
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Device</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{job.devpath ?? 'N/A'}</dd>
					</div>
					<div>
						<dt class="text-gray-500 dark:text-gray-400">{isMusicDisc ? 'Tracks' : 'Titles'}</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{job.no_of_titles ?? 'N/A'}</dd>
					</div>
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Started</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{formatDateTime(job.start_time)}</dd>
					</div>
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Finished</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{formatDateTime(job.stop_time)}</dd>
					</div>
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Duration</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{job.job_length ?? 'N/A'}</dd>
					</div>
				</dl>

				{#if job.logfile}
					<a
						href="/logs/{job.logfile}"
						class="inline-flex items-center gap-1 text-sm text-primary-text hover:underline dark:text-primary-text-dark"
					>
						View Log
					</a>
				{/if}

				{#if job.errors}
					<div class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
						<strong>Errors:</strong> {job.errors}
					</div>
				{/if}
			</div>
		</div>

		<!-- Auto vs Manual title info -->
		{#if hasAutoManualDiff}
			<div class="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm dark:border-amber-800 dark:bg-amber-900/20">
				<svg class="h-4 w-4 flex-shrink-0 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
				<span class="text-amber-800 dark:text-amber-300">
					Auto-detected: <span class="font-medium">{job.title_auto}{#if job.year_auto} ({job.year_auto}){/if}</span>
				</span>
			</div>
		{/if}

		<!-- Title search / edit -->
		{#if isVideoDisc}
			{#if !showTitleSearch}
				<button
					onclick={() => (showTitleSearch = true)}
					class="rounded-lg px-3 py-1.5 text-sm font-medium bg-indigo-100 text-indigo-700 hover:bg-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 dark:hover:bg-indigo-900/50 transition-colors"
				>
					Search / Edit Title
				</button>
			{:else}
				<section class="rounded-lg border border-primary/20 p-4 dark:border-primary/20">
					<div class="mb-3 flex items-center justify-between">
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Search / Edit Title</h2>
						<button
							onclick={() => (showTitleSearch = false)}
							aria-label="Close title search"
							class="rounded p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
						>
							<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>
					<TitleSearch {job} onapply={handleTitleApply} />
				</section>
			{/if}
		{/if}

		<!-- Rip Settings -->
		{#if job.config}
			{#if !showRipSettings}
				<button
					onclick={() => (showRipSettings = true)}
					class="rounded-lg px-3 py-1.5 text-sm font-medium bg-primary/5 text-gray-700 ring-1 ring-primary/25 hover:bg-primary/10 dark:bg-primary/10 dark:text-gray-200 dark:ring-primary/30 dark:hover:bg-primary/15 transition-colors"
				>
					Rip Settings
				</button>
			{:else}
				<section class="rounded-lg border border-primary/20 p-4 dark:border-primary/20">
					<div class="mb-3 flex items-center justify-between">
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Rip Settings</h2>
						<button
							onclick={() => (showRipSettings = false)}
							class="rounded p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
							aria-label="Close rip settings"
						>
							<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>
					<RipSettings {job} config={job.config} onsaved={handleConfigSaved} />
				</section>
			{/if}
		{/if}

		<!-- Tracks -->
		{#if job.tracks.length > 0}
			<section>
				<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Tracks ({job.tracks.length})</h2>
				<div class="overflow-x-auto rounded-lg border border-primary/20 dark:border-primary/20">
					<table class="w-full text-left text-sm">
						<thead class="bg-page text-gray-600 dark:bg-primary/5 dark:text-gray-400">
							<tr>
								<th class="px-4 py-3 font-medium">#</th>
								<th class="px-4 py-3 font-medium">{isMusicDisc ? 'Title' : 'Filename'}</th>
								<th class="px-4 py-3 font-medium">{isMusicDisc ? 'Duration' : 'Length'}</th>
								{#if isMusicDisc}
									<th class="px-4 py-3 font-medium">Format</th>
								{:else}
									<th class="px-4 py-3 font-medium">Aspect</th>
									<th class="px-4 py-3 font-medium">FPS</th>
									<th class="px-4 py-3 font-medium">Main</th>
								{/if}
								<th class="px-4 py-3 font-medium">Ripped</th>
								<th class="px-4 py-3 font-medium">Status</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
							{#each job.tracks as track}
								<tr class="hover:bg-page dark:hover:bg-gray-800/50">
									<td class="px-4 py-3">{track.track_number ?? ''}</td>
									{#if isMusicDisc}
										<td class="max-w-[300px] truncate px-4 py-3">{(track.basename ?? track.filename ?? '').replace(/^\d+-/, '').replace(/\.\w+$/, '').replace(/_/g, ' ')}</td>
									{:else}
										<td class="max-w-[200px] truncate px-4 py-3 font-mono text-xs">{track.filename ?? track.basename ?? ''}</td>
									{/if}
									<td class="px-4 py-3">{track.length != null ? `${Math.floor(track.length / 60)}:${String(track.length % 60).padStart(2, '0')}` : ''}</td>
									{#if isMusicDisc}
										<td class="px-4 py-3 uppercase text-xs">{track.source ?? ''}</td>
									{:else}
										<td class="px-4 py-3">{track.aspect_ratio ?? ''}</td>
										<td class="px-4 py-3">{track.fps ?? ''}</td>
										<td class="px-4 py-3">{track.main_feature ? 'Yes' : ''}</td>
									{/if}
									<td class="px-4 py-3">{track.ripped ? 'Yes' : 'No'}</td>
									<td class="px-4 py-3"><StatusBadge status={track.status} /></td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</section>
		{/if}

		<!-- Config -->
		{#if job.config}
			<section>
				<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Configuration</h2>
				<div class="overflow-x-auto rounded-lg border border-primary/20 dark:border-primary/20">
					<table class="w-full text-left text-sm">
						<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
							{#each Object.entries(job.config) as [key, value]}
								<tr class="hover:bg-page dark:hover:bg-gray-800/50">
									<td class="px-4 py-2 font-mono text-xs font-medium text-gray-500 dark:text-gray-400">{key}</td>
									<td class="px-4 py-2 text-gray-900 dark:text-white">{value ?? ''}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</section>
		{/if}
	</div>
{/if}
