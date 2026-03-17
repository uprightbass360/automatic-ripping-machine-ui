<script lang="ts">
import { onMount } from 'svelte';
import { fetchLogs, fetchTranscoderLogs, deleteLog } from '$lib/api/logs';
import type { LogFile } from '$lib/types/arm';
import { formatBytes, formatDateTime } from '$lib/utils/format';

let activeTab = $state<'arm' | 'transcoder'>('arm');
let armLogs = $state<LogFile[]>([]);
let transcoderLogs = $state<LogFile[]>([]);
let armError = $state<string | null>(null);
let transcoderError = $state<string | null>(null);

let fileSortKey = $state<keyof LogFile>('modified');
let fileSortDir = $state<'asc' | 'desc'>('desc');

let deleteDialog = { open: false, filename: '', tab: '' };
let feedback: { type: 'success' | 'error'; message: string } | null = null;

function handleDeleteRequest(filename: string, tab: 'arm' | 'transcoder') {
	deleteDialog = { open: true, filename, tab };
}

async function confirmDelete() {
	try {
		await deleteLog(deleteDialog.filename);
		feedback = { type: 'success', message: `Deleted ${deleteDialog.filename}` };
		deleteDialog = { open: false, filename: '', tab: '' };
		// Refresh logs
		if (deleteDialog.tab === 'arm') {
			armLogs = await fetchLogs();
		} else {
			transcoderLogs = await fetchTranscoderLogs();
		}
	} catch (e) {
		feedback = { type: 'error', message: e instanceof Error ? e.message : 'Delete failed' };
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

function switchTab(tab: 'arm' | 'transcoder') {
	activeTab = tab;
	fileSortKey = 'modified';
	fileSortDir = 'desc';
}

onMount(async () => {
	try {
		armLogs = await fetchLogs();
	} catch (e) {
		armError = e instanceof Error ? e.message : 'Failed to load ARM logs';
	}
	try {
		transcoderLogs = await fetchTranscoderLogs();
	} catch (e) {
		transcoderError = e instanceof Error ? e.message : 'Failed to load transcoder logs';
	}
});

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
								<td class="px-4 py-3">
									<button class="text-red-500 hover:text-red-700" title="Delete log"
										onclick={() => handleDeleteRequest(log.filename, 'arm')}>🗑️</button>
								</td>
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
		{:else if transcoderLogs.length === 0}
			<p class="py-8 text-center text-gray-400">No transcoder log files found.</p>
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
								<td class="px-4 py-3">
									<button class="text-red-500 hover:text-red-700" title="Delete log"
										onclick={() => handleDeleteRequest(log.filename, 'transcoder')}>🗑️</button>
								</td>
							</tr>
						{/each}
					</tbody>
			</tbody>
		</table>
	</div>
	{/if}
	{/if}
	{#if deleteDialog.open}
		<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
			<div class="rounded-lg bg-white p-6 shadow-xl dark:bg-gray-900">
				<h2 class="mb-4 text-lg font-bold">Delete Log File</h2>
				<p>Are you sure you want to delete <span class="font-mono text-red-500">{deleteDialog.filename}</span>?</p>
				<div class="mt-6 flex gap-4">
					<button class="px-4 py-2 rounded bg-red-500 text-white hover:bg-red-700" onclick={confirmDelete}>Delete</button>
					<button class="px-4 py-2 rounded bg-gray-300 hover:bg-gray-400 dark:bg-gray-700 dark:hover:bg-gray-600" onclick={() => deleteDialog = { open: false, filename: '', tab: '' }}>Cancel</button>
				</div>
			</div>
		</div>
	{/if}
	{#if feedback}
		<div class="fixed bottom-4 left-1/2 z-50 -translate-x-1/2 rounded bg-gray-900 px-4 py-2 text-white shadow-lg">
			{feedback.message}
		</div>
	{/if}
// ...existing code...
