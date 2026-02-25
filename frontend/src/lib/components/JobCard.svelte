<script lang="ts">
	import type { Job } from '$lib/types/arm';
	import StatusBadge from './StatusBadge.svelte';
	import TimeAgo from './TimeAgo.svelte';
	import { elapsedTime } from '$lib/utils/format';
	import { getVideoTypeConfig, isJobActive, discTypeLabel } from '$lib/utils/job-type';
	import DiscTypeIcon from './DiscTypeIcon.svelte';

	interface Props {
		job: Job;
		driveNames?: Record<string, string>;
		progress?: number | null;
		progressStage?: string | null;
	}

	let { job, driveNames = {}, progress = null, progressStage = null }: Props = $props();
	let driveName = $derived(job.devpath ? driveNames[job.devpath] : null);

	let typeConfig = $derived(getVideoTypeConfig(job.video_type));
	let active = $derived(isJobActive(job.status));
	let hasErrors = $derived(!!job.errors && job.errors.trim().length > 0);
	let discLabelDiffers = $derived(
		!!job.label && !!job.title && job.label.toLowerCase() !== job.title.toLowerCase()
	);
</script>

<a
	href="/jobs/{job.job_id}"
	class="block rounded-lg border border-primary/20 border-l-4 {typeConfig.accentBorder} bg-surface p-4 shadow-sm transition hover:shadow-md dark:border-primary/20 dark:bg-surface-dark"
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
				<svg class="h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
					<circle cx="12" cy="12" r="10" />
					<circle cx="12" cy="12" r="3" />
					<circle cx="12" cy="12" r="6.5" stroke-width="0.75" opacity="0.4" />
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
					<button
						onclick={(e) => { e.preventDefault(); e.stopPropagation(); window.open(`https://www.imdb.com/title/${job.imdb_id}/`, '_blank', 'noopener,noreferrer'); }}
						class="inline-flex items-center rounded bg-yellow-400 px-1.5 py-0.5 text-xs font-bold text-black hover:bg-yellow-300"
					>IMDb</button>
				{/if}
				{#if discLabelDiffers}
					<span class="truncate font-mono text-xs text-gray-400 dark:text-gray-500">{job.label}</span>
				{/if}
			</div>

			<!-- Row 3: Active → stage/titles/elapsed; Completed → duration/finish -->
			<div class="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500 dark:text-gray-400">
				{#if active}
					{#if job.stage}
						<span class="rounded bg-primary-light-bg px-1.5 py-0.5 font-medium text-primary-text dark:bg-primary-light-bg-dark/20 dark:text-primary-text-dark">{job.stage}</span>
					{/if}
					{#if job.status === 'info'}
						<span>Scanning{job.no_of_titles ? `... ${job.no_of_titles} titles` : '...'}</span>
					{:else if job.tracks_total != null && job.tracks_total > 0}
						<span>{job.tracks_ripped ?? 0} / {job.tracks_total} titles</span>
					{:else if job.no_of_titles != null}
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
					<span class="inline-flex items-center gap-1 rounded bg-primary/10 px-1.5 py-0.5 dark:bg-primary/15">
						<DiscTypeIcon disctype={job.disctype} size="h-3.5 w-3.5" />
						{discTypeLabel(job.disctype)}
					</span>
				{/if}
				{#if job.devpath}
					<span>{driveName ?? job.devpath}</span>
				{/if}
				{#if !active && job.start_time}
					<TimeAgo date={job.start_time} />
				{/if}
			</div>
		</div>
	</div>
	{#if active}
		<div class="mt-3">
			{#if progress != null && progress > 0}
				<div class="flex items-center gap-2">
					<div class="h-1.5 flex-1 overflow-hidden rounded-full bg-primary/15 dark:bg-primary/15">
						<div class="h-full rounded-full bg-primary transition-all duration-500" style="width: {Math.min(progress, 100)}%"></div>
					</div>
					<span class="flex-shrink-0 text-xs font-medium text-primary-text dark:text-primary-text-dark">{progress.toFixed(1)}%</span>
				</div>
				{#if progressStage}
					<p class="mt-0.5 text-xs text-gray-400 dark:text-gray-500">{progressStage}</p>
				{/if}
			{:else}
				<div class="h-1.5 overflow-hidden rounded-full bg-primary/15 dark:bg-primary/15">
					<div class="h-full w-1/3 animate-indeterminate rounded-full bg-primary/60"></div>
				</div>
			{/if}
		</div>
	{/if}
</a>
