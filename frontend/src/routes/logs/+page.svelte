<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchLogs } from '$lib/api/logs';
	import type { LogFile } from '$lib/types/arm';
	import { formatBytes, formatDateTime } from '$lib/utils/format';

	let logs = $state<LogFile[]>([]);
	let error = $state<string | null>(null);

	onMount(async () => {
		try {
			logs = await fetchLogs();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load logs';
		}
	});
</script>

<svelte:head>
	<title>Logs - ARM UI</title>
</svelte:head>

<div class="space-y-4">
	<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Log Files</h1>

	{#if error}
		<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
			{error}
		</div>
	{:else if logs.length === 0}
		<p class="py-8 text-center text-gray-400">No log files found.</p>
	{:else}
		<div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
			<table class="w-full text-left text-sm">
				<thead class="bg-gray-50 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
					<tr>
						<th class="px-4 py-3 font-medium">Filename</th>
						<th class="px-4 py-3 font-medium">Size</th>
						<th class="px-4 py-3 font-medium">Last Modified</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
					{#each logs as log}
						<tr class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
							<td class="px-4 py-3">
								<a href="/logs/{log.filename}" class="text-blue-600 hover:underline dark:text-blue-400">
									{log.filename}
								</a>
							</td>
							<td class="px-4 py-3 text-gray-500 dark:text-gray-400">{formatBytes(log.size)}</td>
							<td class="px-4 py-3 text-gray-500 dark:text-gray-400">{formatDateTime(log.modified)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>
