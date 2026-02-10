<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { fetchJob } from '$lib/api/jobs';
	import type { JobDetail } from '$lib/types/arm';
	import JobActions from '$lib/components/JobActions.svelte';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import { formatDateTime, timeAgo } from '$lib/utils/format';

	let job = $state<JobDetail | null>(null);
	let error = $state<string | null>(null);

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

	onMount(() => {
		loadJob();
	});
</script>

<svelte:head>
	<title>{job?.title || 'Job Detail'} - ARM UI</title>
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
		<a href="/jobs" class="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline dark:text-blue-400">
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

				{#if job.imdb_id}
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
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Video Type</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{job.video_type ?? 'N/A'}</dd>
					</div>
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Disc Type</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{job.disctype ?? 'N/A'}</dd>
					</div>
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Device</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{job.devpath ?? 'N/A'}</dd>
					</div>
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Titles</dt>
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
						class="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline dark:text-blue-400"
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

		<!-- Tracks -->
		{#if job.tracks.length > 0}
			<section>
				<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Tracks ({job.tracks.length})</h2>
				<div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
					<table class="w-full text-left text-sm">
						<thead class="bg-gray-50 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
							<tr>
								<th class="px-4 py-3 font-medium">#</th>
								<th class="px-4 py-3 font-medium">Filename</th>
								<th class="px-4 py-3 font-medium">Length</th>
								<th class="px-4 py-3 font-medium">Aspect</th>
								<th class="px-4 py-3 font-medium">FPS</th>
								<th class="px-4 py-3 font-medium">Main</th>
								<th class="px-4 py-3 font-medium">Ripped</th>
								<th class="px-4 py-3 font-medium">Status</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
							{#each job.tracks as track}
								<tr class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
									<td class="px-4 py-3">{track.track_number ?? ''}</td>
									<td class="max-w-[200px] truncate px-4 py-3 font-mono text-xs">{track.filename ?? track.basename ?? ''}</td>
									<td class="px-4 py-3">{track.length != null ? `${Math.floor(track.length / 60)}m ${track.length % 60}s` : ''}</td>
									<td class="px-4 py-3">{track.aspect_ratio ?? ''}</td>
									<td class="px-4 py-3">{track.fps ?? ''}</td>
									<td class="px-4 py-3">{track.main_feature ? 'Yes' : ''}</td>
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
				<div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
					<table class="w-full text-left text-sm">
						<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
							{#each Object.entries(job.config) as [key, value]}
								<tr class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
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
