<script lang="ts">
	import type { JobStats } from '$lib/api/jobs';

	interface Props {
		selectedJobs: Set<number>;
		jobsStats: JobStats | null;
		gearOpen: boolean;
		bulkBusy: boolean;
		onaction: (
			action: 'delete' | 'purge',
			params: { job_ids?: number[]; status?: string },
			description: string
		) => void;
		ontoggle: () => void;
	}

	let { selectedJobs, jobsStats, gearOpen, bulkBusy, onaction, ontoggle }: Props = $props();

	const pillBase = 'px-2.5 py-1 rounded-md text-xs font-semibold cursor-pointer transition-colors';
</script>

<!-- Selection count -->
{#if selectedJobs.size > 0}
	<span class="text-sm font-medium text-gray-600 dark:text-gray-300">{selectedJobs.size} selected</span>
{/if}

<!-- Gear menu -->
<div class="relative">
	<button
		onclick={(e: MouseEvent) => { e.stopPropagation(); ontoggle(); }}
		disabled={bulkBusy}
		class="{pillBase} inline-flex items-center gap-1 bg-primary/10 text-gray-700 hover:bg-primary/20 dark:bg-primary/15 dark:text-gray-300 dark:hover:bg-primary/25 disabled:opacity-50"
	>
		{#if bulkBusy}
			<span class="inline-block h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent"></span>
		{:else}
			&#9881;
		{/if}
		Actions &#9662;
	</button>

	{#if gearOpen}
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div
			onclick={(e: MouseEvent) => e.stopPropagation()}
			class="absolute right-0 z-50 mt-1 w-56 rounded-lg border border-primary/20 bg-surface py-1 shadow-lg dark:border-primary/25 dark:bg-surface-dark"
		>
			{#if selectedJobs.size > 0}
				<div class="px-3 py-1.5 text-xs font-semibold text-gray-400 dark:text-gray-500">Selected ({selectedJobs.size})</div>
				<button
					onclick={() => onaction('delete', { job_ids: [...selectedJobs] }, `delete ${selectedJobs.size} selected job(s)`)}
					class="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-primary/5 dark:text-gray-300 dark:hover:bg-primary/10"
				>Delete Selected</button>
				<button
					onclick={() => onaction('purge', { job_ids: [...selectedJobs] }, `purge ${selectedJobs.size} selected job(s) and their files`)}
					class="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
				>Purge Selected</button>
				<div class="my-1 border-t border-gray-200 dark:border-gray-700"></div>
			{/if}

			<div class="px-3 py-1.5 text-xs font-semibold text-gray-400 dark:text-gray-500">Bulk Actions</div>
			<button
				onclick={() => onaction('delete', { status: 'fail' }, `delete all failed jobs${jobsStats?.fail ? ` (${jobsStats.fail})` : ''}`)}
				class="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-primary/5 dark:text-gray-300 dark:hover:bg-primary/10"
			>Delete All Failed{#if jobsStats?.fail} ({jobsStats.fail}){/if}</button>
			<button
				onclick={() => onaction('purge', { status: 'fail' }, `purge all failed jobs and their files`)}
				class="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
			>Purge All Failed</button>
			<button
				onclick={() => onaction('delete', { status: 'success' }, `delete all successful jobs${jobsStats?.success ? ` (${jobsStats.success})` : ''}`)}
				class="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-primary/5 dark:text-gray-300 dark:hover:bg-primary/10"
			>Delete All Successful{#if jobsStats?.success} ({jobsStats.success}){/if}</button>
		</div>
	{/if}
</div>
