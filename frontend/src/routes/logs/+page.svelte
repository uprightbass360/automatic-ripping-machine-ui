<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchLogs, fetchTranscoderLogs } from '$lib/api/logs';
	import type { LogFile } from '$lib/types/arm';
	import { formatBytes, formatDateTime } from '$lib/utils/format';

	let activeTab = $state<'arm' | 'transcoder'>('arm');
	let armLogs = $state<LogFile[]>([]);
	let transcoderLogs = $state<LogFile[]>([]);
	let armError = $state<string | null>(null);
	let transcoderError = $state<string | null>(null);
	let transcoderLoaded = $state(false);

	let fileSortKey = $state<keyof LogFile>('modified');
	let fileSortDir = $state<'asc' | 'desc'>('desc');

	function toggleFileSort(key: keyof LogFile) {
		if (fileSortKey === key) {
			fileSortDir = fileSortDir === 'asc' ? 'desc' : 'asc';
		} else {
			fileSortKey = key;
			fileSortDir = key === 'modified' ? 'desc' : 'asc';
		}
	}

	function sortLogFiles(files: LogFile[]): LogFile[] {
		return [...files].sort((a, b) => {
			const av = a[fileSortKey];
			const bv = b[fileSortKey];
			let cmp: number;
			if (fileSortKey === 'size') {
				cmp = (av as number) - (bv as number);
			} else {
				cmp = String(av).localeCompare(String(bv));
			}
			return fileSortDir === 'asc' ? cmp : -cmp;
		});
	}

	let sortedArmLogs = $derived(sortLogFiles(armLogs));
	let sortedTranscoderLogs = $derived(sortLogFiles(transcoderLogs));

	onMount(async () => {
		try {
			armLogs = await fetchLogs();
		} catch (e) {
			armError = e instanceof Error ? e.message : 'Failed to load ARM logs';
		}
	});

	async function loadTranscoderLogs() {
		if (transcoderLoaded) return;
		try {
			transcoderLogs = await fetchTranscoderLogs();
		} catch (e) {
			transcoderError = e instanceof Error ? e.message : 'Failed to load transcoder logs';
		}
		transcoderLoaded = true;
	}

	function switchTab(tab: 'arm' | 'transcoder') {
		activeTab = tab;
		if (tab === 'transcoder') {
			loadTranscoderLogs();
		}
	}
</script>

<svelte:head>
	<title>ARM - Logs</title>
</svelte:head>

<div class="space-y-4">
	<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Log Files</h1>

	<!-- Tab Bar -->
	<div class="border-b border-primary/20 dark:border-primary/20">
		<nav class="-mb-px flex gap-4" aria-label="Log tabs">
			<button
				type="button"
				onclick={() => switchTab('arm')}
				class="whitespace-nowrap border-b-2 px-1 py-2.5 text-sm font-medium transition-colors
					{activeTab === 'arm'
					? 'border-primary text-primary-text dark:border-primary-text-dark dark:text-primary-text-dark'
					: 'border-transparent text-gray-500 hover:border-primary/30 hover:text-gray-700 dark:text-gray-400 dark:hover:border-primary/30 dark:hover:text-gray-300'}"
			>
				ARM Ripper
			</button>
			<button
				type="button"
				onclick={() => switchTab('transcoder')}
				class="whitespace-nowrap border-b-2 px-1 py-2.5 text-sm font-medium transition-colors
					{activeTab === 'transcoder'
					? 'border-primary text-primary-text dark:border-primary-text-dark dark:text-primary-text-dark'
					: 'border-transparent text-gray-500 hover:border-primary/30 hover:text-gray-700 dark:text-gray-400 dark:hover:border-primary/30 dark:hover:text-gray-300'}"
			>
				Transcoder
			</button>
		</nav>
	</div>

	{#if activeTab === 'arm'}
		{#if armError}
			<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
				{armError}
			</div>
		{:else if armLogs.length === 0}
			<p class="py-8 text-center text-gray-400">No log files found.</p>
		{:else}
			<div class="overflow-x-auto rounded-lg border border-primary/20 dark:border-primary/20">
				<table class="w-full text-left text-sm">
					<thead class="bg-page text-gray-600 dark:bg-primary/5 dark:text-gray-400">
						<tr>
							<th class="cursor-pointer select-none px-4 py-3 font-medium" onclick={() => toggleFileSort('filename')}>
								Filename
								<span class="ml-0.5 text-[10px]">{fileSortKey === 'filename' ? (fileSortDir === 'asc' ? '▲' : '▼') : '▲▼'}</span>
							</th>
							<th class="cursor-pointer select-none px-4 py-3 font-medium" onclick={() => toggleFileSort('size')}>
								Size
								<span class="ml-0.5 text-[10px]">{fileSortKey === 'size' ? (fileSortDir === 'asc' ? '▲' : '▼') : '▲▼'}</span>
							</th>
							<th class="cursor-pointer select-none px-4 py-3 font-medium" onclick={() => toggleFileSort('modified')}>
								Last Modified
								<span class="ml-0.5 text-[10px]">{fileSortKey === 'modified' ? (fileSortDir === 'asc' ? '▲' : '▼') : '▲▼'}</span>
							</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
						{#each sortedArmLogs as log}
							<tr class="hover:bg-page dark:hover:bg-gray-800/50">
								<td class="px-4 py-3">
									<a href="/logs/{log.filename}" class="text-primary-text hover:underline dark:text-primary-text-dark">
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
	{:else}
		{#if transcoderError}
			<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
				{transcoderError}
			</div>
		{:else if !transcoderLoaded}
			<div class="flex items-center justify-center p-8 text-gray-400">
				<svg class="mr-2 h-5 w-5 animate-spin" viewBox="0 0 24 24">
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
					<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
				</svg>
				Loading...
			</div>
		{:else if transcoderLogs.length === 0}
			<p class="py-8 text-center text-gray-400">Transcoder offline or no logs available.</p>
		{:else}
			<div class="overflow-x-auto rounded-lg border border-primary/20 dark:border-primary/20">
				<table class="w-full text-left text-sm">
					<thead class="bg-page text-gray-600 dark:bg-primary/5 dark:text-gray-400">
						<tr>
							<th class="cursor-pointer select-none px-4 py-3 font-medium" onclick={() => toggleFileSort('filename')}>
								Filename
								<span class="ml-0.5 text-[10px]">{fileSortKey === 'filename' ? (fileSortDir === 'asc' ? '▲' : '▼') : '▲▼'}</span>
							</th>
							<th class="cursor-pointer select-none px-4 py-3 font-medium" onclick={() => toggleFileSort('size')}>
								Size
								<span class="ml-0.5 text-[10px]">{fileSortKey === 'size' ? (fileSortDir === 'asc' ? '▲' : '▼') : '▲▼'}</span>
							</th>
							<th class="cursor-pointer select-none px-4 py-3 font-medium" onclick={() => toggleFileSort('modified')}>
								Last Modified
								<span class="ml-0.5 text-[10px]">{fileSortKey === 'modified' ? (fileSortDir === 'asc' ? '▲' : '▼') : '▲▼'}</span>
							</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
						{#each sortedTranscoderLogs as log}
							<tr class="hover:bg-page dark:hover:bg-gray-800/50">
								<td class="px-4 py-3">
									<a href="/logs/transcoder/{log.filename}" class="text-primary-text hover:underline dark:text-primary-text-dark">
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
	{/if}
</div>
