<script lang="ts">
	import type { TranscoderJob } from '$lib/types/transcoder';
	import StatusBadge from './StatusBadge.svelte';
	import ProgressBar from './ProgressBar.svelte';
	import { elapsedTime } from '$lib/utils/format';

	interface Props {
		job: TranscoderJob;
	}

	let { job }: Props = $props();

	let displayTitle = $derived(
		job.title || job.source_path?.split('/').pop() || `Transcode #${job.id}`
	);
</script>

<div class="rounded-lg border border-primary/20 border-l-4 border-l-indigo-500 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
	<div class="flex gap-4">
		<div class="flex h-24 w-16 shrink-0 items-center justify-center rounded-sm bg-indigo-100 text-indigo-400 dark:bg-indigo-900/30 dark:text-indigo-500">
			<svg class="h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
				<path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
			</svg>
		</div>
		<div class="min-w-0 flex-1">
			<!-- Row 1: Title + Status -->
			<div class="flex items-start justify-between gap-2">
				<h3 class="truncate font-semibold text-gray-900 dark:text-white">
					{displayTitle}
				</h3>
				<StatusBadge status={job.status} />
			</div>

			<!-- Row 2: Source file -->
			{#if job.source_path && job.title}
				<div class="mt-0.5 truncate font-mono text-xs text-gray-400 dark:text-gray-500">
					{job.source_path.split('/').pop()}
				</div>
			{/if}

			<!-- Row 3: Elapsed time -->
			<div class="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500 dark:text-gray-400">
				<span class="rounded-sm bg-indigo-100 px-1.5 py-0.5 font-medium text-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-400">transcoding</span>
				{#if job.started_at}
					<span>{elapsedTime(job.started_at)}</span>
				{/if}
			</div>

			<!-- Row 4: Error -->
			{#if job.error}
				<div class="mt-1.5 flex items-center gap-0.5 text-xs text-red-500 dark:text-red-400" title={job.error}>
					<svg class="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
						<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
					</svg>
					errors
				</div>
			{/if}
		</div>
	</div>
	{#if typeof job.progress === 'number'}
		<div class="mt-3">
			<ProgressBar value={job.progress} color="bg-indigo-500" />
		</div>
	{/if}
</div>
