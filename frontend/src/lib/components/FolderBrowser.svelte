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
	let filter = $state('');

	let directories = $derived(
		entries
			.filter((e) => e.type === 'directory')
			.filter((e) => !filter || e.name.toLowerCase().includes(filter.toLowerCase()))
	);

	function formatSize(bytes: number): string {
		if (bytes === 0) return '0 B';
		const units = ['B', 'KB', 'MB', 'GB', 'TB'];
		const i = Math.floor(Math.log(bytes) / Math.log(1024));
		return `${(bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0)} ${units[i]}`;
	}

	function isDiscStructureDir(name: string): boolean {
		const upper = name.toUpperCase();
		return upper === 'BDMV' || upper === 'VIDEO_TS' || upper === 'CERTIFICATE' || upper === 'AUDIO_TS';
	}

	/** True if the current listing contains BDMV or VIDEO_TS — this folder IS a disc. */
	let currentIsDisc = $derived(
		entries.some((e) => e.type === 'directory' && (e.name.toUpperCase() === 'BDMV' || e.name.toUpperCase() === 'VIDEO_TS'))
	);

	/** Badge for entries that are disc structure internals. */
	function discBadgeFor(name: string): string | null {
		const upper = name.toUpperCase();
		if (upper === 'BDMV' || upper === 'CERTIFICATE') return 'Blu-ray';
		if (upper === 'VIDEO_TS' || upper === 'AUDIO_TS') return 'DVD';
		return null;
	}

	async function loadDirectory(path: string) {
		loading = true;
		error = null;
		filter = '';
		try {
			const listing = await fetchIngressDirectory(path);
			currentPath = listing.path;
			entries = listing.entries;
		} catch (e) {
			const msg = e instanceof Error ? e.message : 'Failed to load directory';
			error = msg.includes('unreachable') || msg.includes('503')
				? 'ARM service is starting up — try again in a moment'
				: msg;
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
		// Don't drill into disc structure internals
		if (isDiscStructureDir(entry.name)) return;
		const fullPath = currentPath ? `${currentPath}/${entry.name}` : entry.name;
		selectedPath = null;
		loadDirectory(fullPath);
	}

	// When we navigate into a disc folder, auto-select the current path
	$effect(() => {
		if (currentIsDisc && currentPath) {
			selectedPath = currentPath;
			onselect(currentPath);
		}
	});

	function goBack() {
		if (!currentPath || currentPath === ingressPath) return;
		const parent = currentPath.replace(/\/[^/]+$/, '');
		if (!parent || !ingressPath || !parent.startsWith(ingressPath)) return;
		selectedPath = null;
		loadDirectory(parent);
	}

	async function init() {
		loading = true;
		error = null;
		needsConfig = false;
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
			const msg = e instanceof Error ? e.message : 'Failed to load file roots';
			error = msg.includes('unreachable') || msg.includes('503')
				? 'ARM service is starting up — try again in a moment'
				: msg;
			loading = false;
		}
	}

	onMount(() => { init(); });
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
			<p>{error}</p>
			<button
				type="button"
				onclick={init}
				class="mt-2 rounded-md bg-red-100 px-3 py-1 text-xs font-medium text-red-800 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-300 dark:hover:bg-red-900/50"
			>Retry</button>
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

		<!-- Filter -->
		{#if entries.filter(e => e.type === 'directory').length > 5}
			<input
				type="text"
				bind:value={filter}
				placeholder="Filter folders..."
				class="w-full rounded-lg border border-primary/25 bg-primary/5 px-3 py-1.5 text-sm text-gray-900 placeholder-gray-400 focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white dark:placeholder-gray-500"
			/>
		{/if}

		<!-- Disc detected banner -->
		{#if currentIsDisc}
			<div class="rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700 dark:border-green-800 dark:bg-green-900/20 dark:text-green-400">
				Disc folder detected — this folder is ready to import.
			</div>
		{/if}

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
							{@const isStructureDir = isDiscStructureDir(entry.name)}
							{@const badge = discBadgeFor(entry.name)}
							<tr
								class="transition-colors {isStructureDir
									? 'cursor-default opacity-50'
									: `cursor-pointer hover:bg-primary/5 dark:hover:bg-primary/10 ${selectedPath === fullPath ? 'bg-primary/15 dark:bg-primary/15' : ''}`}"
								onclick={() => { if (!isStructureDir) handleSelect(entry); }}
								ondblclick={() => { if (!isStructureDir) handleOpen(entry); }}
							>
								<td class="flex items-center gap-2 px-4 py-2">
									<FileIcon category="directory" />
									<span class="{isStructureDir ? 'text-gray-400 dark:text-gray-500' : 'text-gray-900 dark:text-white'}">{entry.name}</span>
									{#if badge}
										<span class="rounded-sm bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
											{badge}
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
			{#if !currentIsDisc}
				<p class="mt-2 text-xs text-gray-400 dark:text-gray-500">Navigate to a folder containing BDMV or VIDEO_TS and select it.</p>
			{/if}
		{/if}
	{/if}
</div>
