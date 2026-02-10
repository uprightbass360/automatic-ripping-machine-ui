<script lang="ts">
	import type { Drive } from '$lib/types/arm';
	import StatusBadge from './StatusBadge.svelte';

	interface Props {
		drive: Drive;
	}

	let { drive }: Props = $props();
</script>

<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
	<div class="mb-3 flex items-center justify-between">
		<h3 class="font-semibold text-gray-900 dark:text-white">
			{drive.name || drive.mount || `Drive ${drive.drive_id}`}
		</h3>
		{#if drive.current_job}
			<StatusBadge status={drive.current_job.status} />
		{:else}
			<span class="text-xs text-gray-400">Idle</span>
		{/if}
	</div>

	<div class="space-y-1 text-sm text-gray-500 dark:text-gray-400">
		{#if drive.maker || drive.model}
			<p>{[drive.maker, drive.model].filter(Boolean).join(' ')}</p>
		{/if}
		{#if drive.mount}
			<p class="font-mono text-xs">{drive.mount}</p>
		{/if}
	</div>

	<div class="mt-3 flex flex-wrap gap-1.5">
		{#if drive.read_cd}
			<span class="rounded bg-green-100 px-1.5 py-0.5 text-xs text-green-700 dark:bg-green-900/30 dark:text-green-400">CD</span>
		{/if}
		{#if drive.read_dvd}
			<span class="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">DVD</span>
		{/if}
		{#if drive.read_bd}
			<span class="rounded bg-purple-100 px-1.5 py-0.5 text-xs text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">Blu-ray</span>
		{/if}
	</div>

	{#if drive.current_job}
		<div class="mt-3 border-t border-gray-100 pt-3 dark:border-gray-700">
			<a href="/jobs/{drive.current_job.job_id}" class="text-sm text-blue-600 hover:underline dark:text-blue-400">
				{drive.current_job.title || drive.current_job.label || 'Active Job'}
			</a>
		</div>
	{/if}
</div>
