<script lang="ts">
	import type { Job } from '$lib/types/arm';
	import JobActions from './JobActions.svelte';
	import StatusBadge from './StatusBadge.svelte';
	import TimeAgo from './TimeAgo.svelte';
	import { elapsedTime } from '$lib/utils/format';
	import { getVideoTypeConfig, isJobActive } from '$lib/utils/job-type';

	interface Props {
		job: Job;
		onaction?: () => void;
	}

	let { job, onaction }: Props = $props();

	let typeConfig = $derived(getVideoTypeConfig(job.video_type));
	let active = $derived(isJobActive(job.status));
	let hasErrors = $derived(!!job.errors && job.errors.trim().length > 0);
	let discLabelDiffers = $derived(
		!!job.label && !!job.title && job.label.toLowerCase() !== job.title.toLowerCase()
	);
</script>

<tr class="border-b border-gray-200 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800/50">
	<!-- Title -->
	<td class="px-4 py-3">
		<div class="flex items-center gap-2">
			<svg class="h-4 w-4 shrink-0 {typeConfig.iconColor}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={typeConfig.iconPath} />
			</svg>
			<div class="min-w-0">
				<a href="/jobs/{job.job_id}" class="font-medium text-blue-600 hover:underline dark:text-blue-400">
					{job.title || job.label || 'Untitled'}
				</a>
				{#if discLabelDiffers}
					<div class="truncate font-mono text-xs text-gray-400 dark:text-gray-500">{job.label}</div>
				{/if}
			</div>
		</div>
	</td>

	<!-- Year + IMDB -->
	<td class="px-4 py-3 text-sm">
		<div class="flex items-center gap-1.5">
			{#if job.year}
				<span>{job.year}</span>
			{/if}
			{#if job.imdb_id}
				<a
					href="https://www.imdb.com/title/{job.imdb_id}/"
					target="_blank"
					rel="noopener noreferrer"
					class="inline-flex items-center rounded bg-yellow-400 px-1 py-0.5 text-[10px] font-bold leading-none text-black hover:bg-yellow-300"
				>IMDb</a>
			{/if}
		</div>
	</td>

	<!-- Status + stage/error -->
	<td class="px-4 py-3">
		<div>
			<StatusBadge status={job.status} />
			{#if active && job.stage}
				<div class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">{job.stage}</div>
			{/if}
			{#if hasErrors}
				<div class="mt-0.5 flex items-center gap-0.5 text-xs text-red-500 dark:text-red-400" title={job.errors ?? ''}>
					<svg class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
						<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
					</svg>
					errors
				</div>
			{/if}
		</div>
	</td>

	<!-- Type (colored badge) -->
	<td class="px-4 py-3 text-sm">
		<span class="rounded px-1.5 py-0.5 text-xs font-medium {typeConfig.badgeClasses}">{typeConfig.label}</span>
	</td>

	<!-- Disc -->
	<td class="px-4 py-3 text-sm">{job.disctype ?? ''}</td>

	<!-- Device -->
	<td class="px-4 py-3 text-sm">{job.devpath ?? ''}</td>

	<!-- Started + elapsed/duration sub-text -->
	<td class="px-4 py-3 text-sm">
		{#if job.start_time}
			<TimeAgo date={job.start_time} />
			{#if active}
				<div class="text-xs text-gray-400 dark:text-gray-500">{elapsedTime(job.start_time)}</div>
			{:else if job.job_length}
				<div class="text-xs text-gray-400 dark:text-gray-500">{job.job_length}</div>
			{/if}
		{:else}
			N/A
		{/if}
	</td>

	<!-- Actions -->
	<td class="px-4 py-3">
		<JobActions {job} compact {onaction} />
	</td>
</tr>
