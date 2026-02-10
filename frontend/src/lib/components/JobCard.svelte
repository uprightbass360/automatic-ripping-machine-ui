<script lang="ts">
	import type { Job } from '$lib/types/arm';
	import StatusBadge from './StatusBadge.svelte';
	import TimeAgo from './TimeAgo.svelte';
	import { elapsedTime } from '$lib/utils/format';
	import { getVideoTypeConfig, isJobActive } from '$lib/utils/job-type';

	interface Props {
		job: Job;
	}

	let { job }: Props = $props();

	let typeConfig = $derived(getVideoTypeConfig(job.video_type));
	let active = $derived(isJobActive(job.status));
	let hasErrors = $derived(!!job.errors && job.errors.trim().length > 0);
	let discLabelDiffers = $derived(
		!!job.label && !!job.title && job.label.toLowerCase() !== job.title.toLowerCase()
	);
</script>

<a
	href="/jobs/{job.job_id}"
	class="block rounded-lg border border-gray-200 border-l-4 {typeConfig.accentBorder} bg-white p-4 shadow-sm transition hover:shadow-md dark:border-gray-700 dark:bg-gray-800"
>
	<div class="flex gap-4">
		{#if job.poster_url}
			<img
				src={job.poster_url}
				alt={job.title ?? 'Poster'}
				class="h-24 w-16 rounded object-cover"
			/>
		{:else}
			<div class="flex h-24 w-16 items-center justify-center rounded {typeConfig.placeholderClasses}">
				<svg class="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={typeConfig.iconPath} />
				</svg>
			</div>
		{/if}
		<div class="min-w-0 flex-1">
			<!-- Row 1: Title + Status -->
			<div class="flex items-start justify-between gap-2">
				<h3 class="truncate font-semibold text-gray-900 dark:text-white">
					{job.title || job.label || 'Untitled'}
				</h3>
				<StatusBadge status={job.status} />
			</div>

			<!-- Row 2: Year, IMDB, disc label -->
			<div class="mt-0.5 flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
				{#if job.year}
					<span>{job.year}</span>
				{/if}
				{#if job.imdb_id}
					<a
						href="https://www.imdb.com/title/{job.imdb_id}/"
						target="_blank"
						rel="noopener noreferrer"
						onclick={(e) => e.stopPropagation()}
						class="inline-flex items-center rounded bg-yellow-400 px-1.5 py-0.5 text-xs font-bold text-black hover:bg-yellow-300"
					>IMDb</a>
				{/if}
				{#if discLabelDiffers}
					<span class="truncate font-mono text-xs text-gray-400 dark:text-gray-500">{job.label}</span>
				{/if}
			</div>

			<!-- Row 3: Active → stage/titles/elapsed; Completed → duration/finish -->
			<div class="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500 dark:text-gray-400">
				{#if active}
					{#if job.stage}
						<span class="rounded bg-blue-50 px-1.5 py-0.5 font-medium text-blue-600 dark:bg-blue-900/20 dark:text-blue-400">{job.stage}</span>
					{/if}
					{#if job.no_of_titles != null}
						<span>{job.no_of_titles} title{job.no_of_titles === 1 ? '' : 's'}</span>
					{/if}
					{#if job.start_time}
						<span>{elapsedTime(job.start_time)}</span>
					{/if}
				{:else}
					{#if job.job_length}
						<span>{job.job_length}</span>
					{/if}
					{#if job.stop_time}
						<TimeAgo date={job.stop_time} />
					{/if}
				{/if}
				{#if hasErrors}
					<span class="inline-flex items-center gap-0.5 text-red-500 dark:text-red-400" title={job.errors ?? ''}>
						<svg class="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
						</svg>
						errors
					</span>
				{/if}
			</div>

			<!-- Row 4: Type badge, disctype, device, start time -->
			<div class="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-xs text-gray-500 dark:text-gray-400">
				<span class="rounded px-1.5 py-0.5 font-medium {typeConfig.badgeClasses}">{typeConfig.label}</span>
				{#if job.disctype}
					<span class="rounded bg-gray-100 px-1.5 py-0.5 dark:bg-gray-700">{job.disctype}</span>
				{/if}
				{#if job.devpath}
					<span>{job.devpath}</span>
				{/if}
				{#if !active && job.start_time}
					<TimeAgo date={job.start_time} />
				{/if}
			</div>
		</div>
	</div>
</a>
