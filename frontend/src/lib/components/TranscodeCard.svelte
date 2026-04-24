<script lang="ts">
	import type { TranscoderJob } from '$lib/types/transcoder';
	import StatusBadge from './StatusBadge.svelte';
	import ProgressBar from './ProgressBar.svelte';
	import { elapsedTime } from '$lib/utils/format';
	import { discTypeLabel } from '$lib/utils/job-type';
	import PosterImage from './PosterImage.svelte';
	import DiscTypeIcon from './DiscTypeIcon.svelte';
	import TimeAgo from './TimeAgo.svelte';
	import SkeletonCard from './SkeletonCard.svelte';
	import { slide } from 'svelte/transition';

	interface Props {
		job?: TranscoderJob;
	}

	let { job }: Props = $props();
	let expanded = $state(false);

	let displayTitle = $derived(
		job?.title || job?.source_path?.split('/').pop() || `Transcode #${job?.id}`
	);
	let sourceFile = $derived(job?.source_path?.split('/').pop() ?? null);
	let hasError = $derived(!!job?.error);
	let isActive = $derived(job?.status === 'processing' || job?.status === 'transcoding');

	function toggle(e: MouseEvent) {
		if ((e.target as HTMLElement).closest('a, button:not(.row-toggle)')) return;
		expanded = !expanded;
	}
</script>

{#if !job}
	<SkeletonCard />
{:else}
<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
<div
	class="rounded-lg border border-primary/20 border-l-4 border-l-primary bg-surface shadow-xs transition dark:border-primary/20 dark:bg-surface-dark"
	onclick={toggle}
	role="button"
	tabindex="0"
>
	<!-- Collapsed row -->
	<div class="flex items-center gap-3 px-4 py-2.5 cursor-pointer">
		<!-- Poster thumbnail -->
		<PosterImage url={job.poster_url} alt="" class="h-10 w-7 shrink-0 rounded-sm object-cover" />

		<!-- Title -->
		<h3 class="min-w-0 flex-shrink truncate font-semibold text-sm text-gray-900 dark:text-white">
			{displayTitle}
		</h3>

		<!-- Year -->
		{#if job.year}
			<span class="shrink-0 text-xs text-gray-500 dark:text-gray-400">{job.year}</span>
		{/if}

		<!-- Status badge -->
		<div class="shrink-0">
			<StatusBadge status={job.status} />
		</div>

		<!-- Type + disc badges -->
		<div class="hidden sm:flex shrink-0 items-center gap-1.5">
			{#if job.video_type && job.video_type !== 'unknown'}
				<span class="rounded-sm bg-primary/10 px-1.5 py-0.5 text-xs font-medium dark:bg-primary/15">{job.video_type}</span>
			{/if}
			{#if job.disctype}
				<span class="inline-flex items-center gap-0.5 rounded-sm bg-primary/10 px-1.5 py-0.5 text-xs dark:bg-primary/15">
					<DiscTypeIcon disctype={job.disctype} size="h-3 w-3" />
					{discTypeLabel(job.disctype)}
				</span>
			{/if}
		</div>

		<!-- Progress bar (inline) -->
		{#if typeof job.progress === 'number' && job.progress > 0}
			<div class="hidden lg:block flex-1 min-w-24">
				<ProgressBar value={job.progress} color="bg-primary" />
			</div>
		{:else if isActive}
			<div class="hidden lg:block flex-1 min-w-24">
				<div class="h-2 overflow-hidden rounded-full bg-primary/15">
					<div class="h-full w-1/3 animate-indeterminate rounded-full bg-primary/60"></div>
				</div>
			</div>
		{/if}

		<!-- FPS (when actively encoding) -->
		{#if isActive && typeof job.current_fps === 'number' && job.current_fps > 0}
			<span class="shrink-0 font-mono text-xs text-gray-500 dark:text-gray-400" title="Encoder frames per second">
				{job.current_fps.toFixed(1)} fps
			</span>
		{/if}

		<!-- Elapsed -->
		{#if job.started_at}
			<span class="shrink-0 text-xs text-gray-500 dark:text-gray-400">{elapsedTime(job.started_at)}</span>
		{/if}

		<!-- Error indicator -->
		{#if hasError}
			<span class="shrink-0 text-red-500 dark:text-red-400" title={job.error ?? ''}>
				<svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
					<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
				</svg>
			</span>
		{/if}

		<!-- Expand chevron -->
		<button class="row-toggle shrink-0 p-0.5 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-transform" class:rotate-180={expanded} title={expanded ? 'Collapse' : 'Expand'}>
			<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
			</svg>
		</button>
	</div>

	<!-- Mobile progress -->
	{#if isActive && !expanded}
		<div class="lg:hidden px-4 pb-2.5">
			{#if typeof job.progress === 'number' && job.progress > 0}
				<ProgressBar value={job.progress} color="bg-primary" />
			{:else}
				<div class="h-2 overflow-hidden rounded-full bg-primary/15">
					<div class="h-full w-1/3 animate-indeterminate rounded-full bg-primary/60"></div>
				</div>
			{/if}
		</div>
	{/if}

	<!-- Expanded detail -->
	{#if expanded}
		<div transition:slide={{ duration: 200 }} class="border-t border-primary/10 px-4 py-3 dark:border-primary/15">
			<div class="flex gap-4">
				<PosterImage url={job.poster_url} alt={displayTitle} class="h-32 w-22 shrink-0 rounded-sm object-cover" />

				<div class="min-w-0 flex-1">
					<div class="mb-2">
						<span class="text-sm font-semibold text-gray-900 dark:text-white">{displayTitle}</span>
					</div>

					<table class="w-full text-xs">
						<tbody class="divide-y divide-primary/5 dark:divide-primary/10">
							<tr>
								<td class="py-1 pr-4 text-gray-500 dark:text-gray-400 whitespace-nowrap">Job ID</td>
								<td class="py-1 text-gray-900 dark:text-white">{job.id}{#if job.arm_job_id} <span class="text-gray-400">(ARM #{job.arm_job_id})</span>{/if}</td>
								<td class="py-1 pr-4 text-gray-500 dark:text-gray-400 whitespace-nowrap pl-6">Status</td>
								<td class="py-1"><StatusBadge status={job.status} /></td>
							</tr>
							<tr>
								<td class="py-1 pr-4 text-gray-500 dark:text-gray-400 whitespace-nowrap">Type</td>
								<td class="py-1 text-gray-900 dark:text-white">{job.video_type || '—'}</td>
								<td class="py-1 pr-4 text-gray-500 dark:text-gray-400 whitespace-nowrap pl-6">Disc</td>
								<td class="py-1 text-gray-900 dark:text-white">{job.disctype || '—'}</td>
							</tr>
							<tr>
								<td class="py-1 pr-4 text-gray-500 dark:text-gray-400 whitespace-nowrap">Year</td>
								<td class="py-1 text-gray-900 dark:text-white">{job.year || '—'}</td>
								<td class="py-1 pr-4 text-gray-500 dark:text-gray-400 whitespace-nowrap pl-6">Tracks</td>
								<td class="py-1 text-gray-900 dark:text-white">{job.total_tracks ?? '—'}</td>
							</tr>
							<tr>
								<td class="py-1 pr-4 text-gray-500 dark:text-gray-400 whitespace-nowrap">Source</td>
								<td class="py-1 font-mono text-gray-600 dark:text-gray-400 truncate" title={job.source_path}>{sourceFile || '—'}</td>
								<td class="py-1 pr-4 text-gray-500 dark:text-gray-400 whitespace-nowrap pl-6">Output</td>
								<td class="py-1 font-mono text-gray-600 dark:text-gray-400 truncate" title={job.output_path ?? ''}>{job.output_path?.split('/').pop() || '—'}</td>
							</tr>
							<tr>
								<td class="py-1 pr-4 text-gray-500 dark:text-gray-400 whitespace-nowrap">Started</td>
								<td class="py-1 text-gray-900 dark:text-white">{#if job.started_at}<TimeAgo date={job.started_at} />{:else}—{/if}</td>
								<td class="py-1 pr-4 text-gray-500 dark:text-gray-400 whitespace-nowrap pl-6">
									{#if job.completed_at}Completed{:else}Elapsed{/if}
								</td>
								<td class="py-1 text-gray-900 dark:text-white">
									{#if job.completed_at}
										<TimeAgo date={job.completed_at} />
									{:else if job.started_at}
										{elapsedTime(job.started_at)}
									{:else}
										—
									{/if}
								</td>
							</tr>
							<tr>
								<td class="py-1 pr-4 text-gray-500 dark:text-gray-400 whitespace-nowrap">Progress</td>
								<td class="py-1 text-gray-900 dark:text-white">
									{typeof job.progress === 'number' ? `${job.progress}%` : '—'}
									{#if isActive && typeof job.current_fps === 'number' && job.current_fps > 0}
										<span class="ml-2 font-mono text-xs text-gray-500 dark:text-gray-400">{job.current_fps.toFixed(1)} fps</span>
									{/if}
								</td>
								<td class="py-1 pr-4 text-gray-500 dark:text-gray-400 whitespace-nowrap pl-6">Created</td>
								<td class="py-1 text-gray-900 dark:text-white">{#if job.created_at}<TimeAgo date={job.created_at} />{:else}—{/if}</td>
							</tr>
						</tbody>
					</table>

					{#if hasError}
						<div class="mt-2 flex items-center gap-1 text-xs text-red-500 dark:text-red-400">
							<svg class="h-3.5 w-3.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
							</svg>
							<span>{job.error}</span>
						</div>
					{/if}

					{#if job.arm_job_id}
						<div class="mt-2">
							<a href="/jobs/{job.arm_job_id}" class="inline-block text-xs text-primary hover:underline">View full details</a>
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}
</div>
{/if}
