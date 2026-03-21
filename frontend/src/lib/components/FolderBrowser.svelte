<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { fetchIngressRoot, fetchIngressDirectory } from '$lib/api/folder';
	import { showImportWizard } from '$lib/stores/importWizard';
	import type { FileEntry } from '$lib/types/files';
	import FileIcon from '$lib/components/FileIcon.svelte';

	interface Props {
		onselect: (path: string) => void;
	}

	let { onselect }: Props = $props();

	let ingressPath = $state<string | null>(null);
	let currentPath = $state('');
	let entries = $state<FileEntry[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let needsConfig = $state(false);
	let selectedPath = $state<string | null>(null);

	let directories = $derived(entries.filter((e) => e.type === 'directory'));

	function formatSize(bytes: number): string {
		if (bytes === 0) return '0 B';
		const units = ['B', 'KB', 'MB', 'GB', 'TB'];
		const i = Math.floor(Math.log(bytes) / Math.log(1024));
		return `${(bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0)} ${units[i]}`;
	}

	function isDiscFolder(name: string): string | null {
		const upper = name.toUpperCase();
		if (upper === 'BDMV' || upper === 'CERTIFICATE') return 'BDMV';
		if (upper === 'VIDEO_TS' || upper === 'AUDIO_TS') return 'VIDEO_TS';
		return null;
	}

	async function loadDirectory(path: string) {
		loading = true;
		error = null;
		try {
			const listing = await fetchIngressDirectory(path);
			currentPath = listing.path;
			entries = listing.entries;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load directory';
		} finally {
			loading = false;
		}
	}

	function handleSelect(entry: FileEntry) {
		const fullPath = currentPath ? `${currentPath}/${entry.name}` : entry.name;
		selectedPath = fullPath;
		onselect(fullPath);
	}

	function handleOpen(entry: FileEntry) {
		const fullPath = currentPath ? `${currentPath}/${entry.name}` : entry.name;
		selectedPath = null;
		loadDirectory(fullPath);
	}

	function goBack() {
		if (!currentPath || currentPath === ingressPath) return;
		const parent = currentPath.replace(/\/[^/]+$/, '');
		if (!parent || !ingressPath || !parent.startsWith(ingressPath)) return;
		selectedPath = null;
		loadDirectory(parent);
	}

	onMount(async () => {
		try {
			const roots = await fetchIngressRoot();
			const ingress = roots.find((r) => r.key === 'ingress');
			if (!ingress) {
				needsConfig = true;
				loading = false;
				return;
			}
			ingressPath = ingress.path;
			await loadDirectory(ingress.path);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load file roots';
			loading = false;
		}
	});
</script>

<div class="space-y-3">
	{#if needsConfig}
		<div class="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-400">
			<p class="font-medium">Folder Import Path is not configured</p>
			<p class="mt-1">Set the <strong>Folder Import Path</strong> in
				<button
					type="button"
					class="underline hover:text-amber-900 dark:hover:text-amber-300"
					onclick={() => { showImportWizard.set(false); goto('/settings#ripping/media-directories'); }}
				>Settings &rarr; Ripping &rarr; Media Directories</button>
				to the directory containing your BDMV/VIDEO_TS folders.</p>
		</div>
	{:else if error}
		<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
			{error}
		</div>
	{:else if loading}
		<div class="py-8 text-center text-gray-400">Loading...</div>
	{:else}
		<!-- Breadcrumb -->
		<div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
			{#if currentPath && currentPath !== ingressPath}
				<button
					type="button"
					onclick={goBack}
					class="inline-flex items-center gap-1 text-primary hover:text-primary/80 dark:text-primary dark:hover:text-primary/80"
				>
					<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
					</svg>
					Back
				</button>
				<span class="text-gray-300 dark:text-gray-600">/</span>
			{/if}
			<span class="font-medium text-gray-700 dark:text-gray-300">{currentPath || ingressPath}</span>
		</div>

		<!-- Directory table -->
		{#if directories.length === 0}
			<p class="py-6 text-center text-sm text-gray-400 dark:text-gray-500">No subdirectories found.</p>
		{:else}
			<div class="overflow-x-auto rounded-lg border border-primary/20 dark:border-primary/20">
				<table class="w-full text-left text-sm">
					<thead class="bg-page text-gray-600 dark:bg-primary/5 dark:text-gray-400">
						<tr>
							<th class="px-4 py-2 font-medium">Name</th>
							<th class="px-4 py-2 font-medium">Size</th>
							<th class="px-4 py-2 font-medium">Modified</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
						{#each directories as entry (entry.name)}
							{@const fullPath = currentPath ? `${currentPath}/${entry.name}` : entry.name}
							{@const discBadge = isDiscFolder(entry.name)}
							<tr
								class="cursor-pointer transition-colors hover:bg-primary/5 dark:hover:bg-primary/10 {selectedPath === fullPath ? 'bg-primary/15 dark:bg-primary/15' : ''}"
								onclick={() => handleSelect(entry)}
								ondblclick={() => handleOpen(entry)}
							>
								<td class="flex items-center gap-2 px-4 py-2">
									<FileIcon category="directory" />
									<span class="text-gray-900 dark:text-white">{entry.name}</span>
									{#if discBadge}
										<span class="rounded-sm bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
											{discBadge}
										</span>
									{/if}
								</td>
								<td class="px-4 py-2 text-gray-500 dark:text-gray-400">{formatSize(entry.size)}</td>
								<td class="px-4 py-2 text-gray-500 dark:text-gray-400">
									{new Date(entry.modified).toLocaleDateString()}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	{/if}
</div>
