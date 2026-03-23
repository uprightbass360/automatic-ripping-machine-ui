<script lang="ts">
	import { onMount } from 'svelte';
	import {
		fetchSummary,
		fetchOrphanLogs,
		fetchOrphanFolders,
		deleteLog,
		deleteFolder,
		bulkDeleteLogs,
		bulkDeleteFolders,
		dismissAllNotifications,
		purgeNotifications,
		cleanupTranscoder,
		fetchImageCacheStats,
		clearImageCache,
		type MaintenanceSummary,
		type OrphanLogsResponse,
		type OrphanFoldersResponse,
		type ImageCacheStats
	} from '$lib/api/maintenance';

	let summary = $state<MaintenanceSummary | null>(null);
	let summaryError = $state<string | null>(null);

	// Section expand states
	let logsOpen = $state(false);
	let foldersOpen = $state(false);
	let notificationsOpen = $state(false);
	let transcoderOpen = $state(false);
	let imageCacheOpen = $state(false);

	// Section data (lazy-loaded)
	let logsData = $state<OrphanLogsResponse | null>(null);
	let foldersData = $state<OrphanFoldersResponse | null>(null);
	let logsLoading = $state(false);
	let foldersLoading = $state(false);

	// Image cache
	let cacheStats = $state<ImageCacheStats | null>(null);
	let cacheLoading = $state(false);

	// Selection state
	let selectedLogs = $state<Set<string>>(new Set());
	let selectedFolders = $state<Set<string>>(new Set());

	// Action state
	let busy = $state(false);
	let feedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);

	// Confirm dialog
	let confirmOpen = $state(false);
	let confirmTitle = $state('');
	let confirmMessage = $state('');
	let confirmAction = $state<(() => Promise<void>) | null>(null);

	function formatBytes(bytes: number): string {
		if (bytes === 0) return '0 B';
		const units = ['B', 'KB', 'MB', 'GB', 'TB'];
		const i = Math.floor(Math.log(bytes) / Math.log(1024));
		return `${(bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0)} ${units[i]}`;
	}

	function showConfirm(title: string, message: string, action: () => Promise<void>) {
		confirmTitle = title;
		confirmMessage = message;
		confirmAction = action;
		confirmOpen = true;
	}

	async function executeConfirmed() {
		confirmOpen = false;
		if (!confirmAction) return;
		busy = true;
		feedback = null;
		try {
			await confirmAction();
		} catch (e) {
			feedback = { type: 'error', message: e instanceof Error ? e.message : 'Action failed' };
		} finally {
			busy = false;
			confirmAction = null;
		}
	}

	async function loadSummary() {
		try {
			summary = await fetchSummary();
			summaryError = null;
		} catch (e) {
			summaryError = e instanceof Error ? e.message : 'Failed to load summary';
		}
	}

	async function loadLogs() {
		logsLoading = true;
		try {
			logsData = await fetchOrphanLogs();
			selectedLogs = new Set();
		} catch {
			logsData = null;
		} finally {
			logsLoading = false;
		}
	}

	async function loadFolders() {
		foldersLoading = true;
		try {
			foldersData = await fetchOrphanFolders();
			selectedFolders = new Set();
		} catch {
			foldersData = null;
		} finally {
			foldersLoading = false;
		}
	}

	function toggleLogsSection() {
		logsOpen = !logsOpen;
		if (logsOpen && !logsData && !logsLoading) loadLogs();
	}

	function toggleFoldersSection() {
		foldersOpen = !foldersOpen;
		if (foldersOpen && !foldersData && !foldersLoading) loadFolders();
	}

	function toggleLogSelection(path: string) {
		const next = new Set(selectedLogs);
		if (next.has(path)) next.delete(path);
		else next.add(path);
		selectedLogs = next;
	}

	function toggleFolderSelection(path: string) {
		const next = new Set(selectedFolders);
		if (next.has(path)) next.delete(path);
		else next.add(path);
		selectedFolders = next;
	}

	async function handleDeleteLog(path: string) {
		showConfirm('Delete Log', `Delete ${path.split('/').pop()}?`, async () => {
			await deleteLog(path);
			feedback = { type: 'success', message: 'Log deleted' };
			await loadLogs();
			await loadSummary();
		});
	}

	async function handleDeleteFolder(path: string) {
		const name = path.split('/').pop();
		showConfirm('Delete Folder', `Delete "${name}" and all its contents?`, async () => {
			await deleteFolder(path);
			feedback = { type: 'success', message: `Folder "${name}" deleted` };
			await loadFolders();
			await loadSummary();
		});
	}

	async function handleBulkDeleteLogs() {
		const count = selectedLogs.size;
		showConfirm('Delete Logs', `Delete ${count} selected log file${count !== 1 ? 's' : ''}?`, async () => {
			const result = await bulkDeleteLogs([...selectedLogs]);
			feedback = {
				type: result.errors.length ? 'error' : 'success',
				message: `Deleted ${result.removed.length} log${result.removed.length !== 1 ? 's' : ''}${result.errors.length ? `, ${result.errors.length} error(s)` : ''}`
			};
			await loadLogs();
			await loadSummary();
		});
	}

	async function handleBulkDeleteFolders() {
		const count = selectedFolders.size;
		showConfirm(
			'Delete Folders',
			`Delete ${count} selected folder${count !== 1 ? 's' : ''} and all their contents?`,
			async () => {
				const result = await bulkDeleteFolders([...selectedFolders]);
				feedback = {
					type: result.errors.length ? 'error' : 'success',
					message: `Deleted ${result.removed.length} folder${result.removed.length !== 1 ? 's' : ''}${result.errors.length ? `, ${result.errors.length} error(s)` : ''}`
				};
				await loadFolders();
				await loadSummary();
			}
		);
	}

	async function handleDismissNotifications() {
		showConfirm('Dismiss Notifications', 'Mark all unseen notifications as seen?', async () => {
			const result = await dismissAllNotifications();
			feedback = {
				type: 'success',
				message: `${result.count} notification${result.count !== 1 ? 's' : ''} dismissed`
			};
			await loadSummary();
		});
	}

	async function handlePurgeNotifications() {
		showConfirm(
			'Purge Notifications',
			'Permanently delete all cleared notifications from the database?',
			async () => {
				const result = await purgeNotifications();
				feedback = {
					type: 'success',
					message: `${result.count} notification${result.count !== 1 ? 's' : ''} purged`
				};
				await loadSummary();
			}
		);
	}

	async function handleCleanupTranscoder() {
		showConfirm('Clean Up Transcoder', 'Delete all completed and failed transcoder jobs?', async () => {
			const result = await cleanupTranscoder();
			feedback = {
				type: result.errors.length ? 'error' : 'success',
				message: `Deleted ${result.deleted} job${result.deleted !== 1 ? 's' : ''}${result.errors.length ? `, ${result.errors.length} error(s)` : ''}`
			};
			await loadSummary();
		});
	}

	async function loadCacheStats() {
		cacheLoading = true;
		try {
			cacheStats = await fetchImageCacheStats();
		} catch { cacheStats = null; }
		cacheLoading = false;
	}

	async function handleClearCache() {
		showConfirm('Clear Image Cache', 'Delete all cached poster images? They will be re-fetched on next view.', async () => {
			const result = await clearImageCache();
			feedback = {
				type: 'success',
				message: `Cleared ${result.cleared} cached image${result.cleared !== 1 ? 's' : ''} (${(result.freed_bytes / 1048576).toFixed(1)} MB)`
			};
			cacheStats = await fetchImageCacheStats();
		});
	}

	onMount(loadSummary);
</script>

<svelte:head><title>Maintenance — ARM</title></svelte:head>

<div class="mx-auto max-w-4xl p-4">
	<h1 class="mb-4 text-2xl font-bold text-gray-900 dark:text-white">Maintenance</h1>

	<!-- Feedback -->
	{#if feedback}
		<div
			class="mb-4 rounded-lg px-4 py-2.5 text-sm {feedback.type === 'success'
				? 'bg-green-500/10 text-green-700 dark:text-green-400'
				: 'bg-red-500/10 text-red-700 dark:text-red-400'}"
		>
			{feedback.message}
			<button
				onclick={() => {
					feedback = null;
				}}
				class="ml-2 opacity-60 hover:opacity-100"
			>
				&times;
			</button>
		</div>
	{/if}

	{#if summaryError}
		<div class="mb-4 rounded-lg bg-red-500/10 px-4 py-3 text-sm text-red-700 dark:text-red-400">
			{summaryError}
		</div>
	{/if}

	<div class="space-y-2">
		<!-- Orphan Logs -->
		<div class="rounded-lg border border-primary/15 dark:border-primary/15">
			<button
				onclick={toggleLogsSection}
				class="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-gray-900 transition-colors hover:bg-primary/5 dark:text-white dark:hover:bg-primary/10"
			>
				<div class="flex items-center gap-2">
					<svg class="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
						/>
					</svg>
					Orphan Logs
					{#if summary?.orphan_logs != null}
						<span
							class="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary-text dark:text-primary-text-dark"
							>{summary.orphan_logs}</span
						>
					{:else if summary && summary.orphan_logs === null}
						<span class="text-xs text-gray-400">unavailable</span>
					{/if}
				</div>
				<svg
					class="h-4 w-4 transition-transform {logsOpen ? 'rotate-180' : ''}"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M19 9l-7 7-7-7"
					/>
				</svg>
			</button>
			{#if logsOpen}
				<div class="border-t border-primary/10 px-4 py-3 dark:border-primary/10">
					{#if logsLoading}
						<p class="text-sm text-gray-400">Loading...</p>
					{:else if logsData && logsData.files.length > 0}
						<div class="mb-2 flex items-center justify-between">
							<span class="text-xs text-gray-500 dark:text-gray-400"
								>{logsData.files.length} file{logsData.files.length !== 1 ? 's' : ''} —
								{formatBytes(logsData.total_size_bytes)}</span
							>
							{#if selectedLogs.size > 0}
								<button
									onclick={handleBulkDeleteLogs}
									disabled={busy}
									class="rounded bg-red-500/15 px-2.5 py-1 text-xs font-medium text-red-700 hover:bg-red-500/25 disabled:opacity-50 dark:text-red-400"
									>Delete Selected ({selectedLogs.size})</button
								>
							{/if}
						</div>
						{#each logsData.files as file}
							<div
								class="flex items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-primary/5 dark:hover:bg-primary/10"
							>
								<input
									type="checkbox"
									checked={selectedLogs.has(file.path)}
									onchange={() => toggleLogSelection(file.path)}
									class="h-3.5 w-3.5 rounded border-gray-300 dark:border-gray-600"
								/>
								<span class="flex-1 truncate font-mono text-xs text-gray-700 dark:text-gray-300"
									>{file.relative_path}</span
								>
								<span class="text-xs text-gray-400">{formatBytes(file.size_bytes)}</span>
								<button
									onclick={() => handleDeleteLog(file.path)}
									disabled={busy}
									class="rounded px-2 py-0.5 text-xs text-red-600 hover:bg-red-500/15 disabled:opacity-50 dark:text-red-400"
									>Delete</button
								>
							</div>
						{/each}
					{:else}
						<p class="text-sm text-gray-400 dark:text-gray-500">No orphan log files found.</p>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Orphan Folders -->
		<div class="rounded-lg border border-primary/15 dark:border-primary/15">
			<button
				onclick={toggleFoldersSection}
				class="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-gray-900 transition-colors hover:bg-primary/5 dark:text-white dark:hover:bg-primary/10"
			>
				<div class="flex items-center gap-2">
					<svg class="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
						/>
					</svg>
					Orphan Folders
					{#if summary?.orphan_folders != null}
						<span
							class="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary-text dark:text-primary-text-dark"
							>{summary.orphan_folders}</span
						>
					{:else if summary && summary.orphan_folders === null}
						<span class="text-xs text-gray-400">unavailable</span>
					{/if}
				</div>
				<svg
					class="h-4 w-4 transition-transform {foldersOpen ? 'rotate-180' : ''}"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M19 9l-7 7-7-7"
					/>
				</svg>
			</button>
			{#if foldersOpen}
				<div class="border-t border-primary/10 px-4 py-3 dark:border-primary/10">
					{#if foldersLoading}
						<p class="text-sm text-gray-400">Loading...</p>
					{:else if foldersData && foldersData.folders.length > 0}
						<div class="mb-2 flex items-center justify-between">
							<span class="text-xs text-gray-500 dark:text-gray-400"
								>{foldersData.folders.length} folder{foldersData.folders.length !== 1 ? 's' : ''} —
								{formatBytes(foldersData.total_size_bytes)}</span
							>
							{#if selectedFolders.size > 0}
								<button
									onclick={handleBulkDeleteFolders}
									disabled={busy}
									class="rounded bg-red-500/15 px-2.5 py-1 text-xs font-medium text-red-700 hover:bg-red-500/25 disabled:opacity-50 dark:text-red-400"
									>Delete Selected ({selectedFolders.size})</button
								>
							{/if}
						</div>
						{#each foldersData.folders as folder}
							<div
								class="flex items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-primary/5 dark:hover:bg-primary/10"
							>
								<input
									type="checkbox"
									checked={selectedFolders.has(folder.path)}
									onchange={() => toggleFolderSelection(folder.path)}
									class="h-3.5 w-3.5 rounded border-gray-300 dark:border-gray-600"
								/>
								<span class="flex-1 truncate text-gray-700 dark:text-gray-300">{folder.name}</span>
								<span class="rounded-full bg-gray-500/10 px-1.5 py-0.5 text-[10px] text-gray-500"
									>{folder.category}</span
								>
								<span class="text-xs text-gray-400">{formatBytes(folder.size_bytes)}</span>
								<button
									onclick={() => handleDeleteFolder(folder.path)}
									disabled={busy}
									class="rounded px-2 py-0.5 text-xs text-red-600 hover:bg-red-500/15 disabled:opacity-50 dark:text-red-400"
									>Delete</button
								>
							</div>
						{/each}
					{:else}
						<p class="text-sm text-gray-400 dark:text-gray-500">No orphan folders found.</p>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Notifications -->
		<div class="rounded-lg border border-primary/15 dark:border-primary/15">
			<button
				onclick={() => {
					notificationsOpen = !notificationsOpen;
				}}
				class="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-gray-900 transition-colors hover:bg-primary/5 dark:text-white dark:hover:bg-primary/10"
			>
				<div class="flex items-center gap-2">
					<svg class="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
						/>
					</svg>
					Notifications
					{#if summary}
						{#if summary.unseen_notifications != null || summary.cleared_notifications != null}
							<span class="text-xs text-gray-500 dark:text-gray-400">
								{#if summary.unseen_notifications != null}{summary.unseen_notifications} unseen{/if}{#if summary.unseen_notifications != null && summary.cleared_notifications != null},
								{/if}{#if summary.cleared_notifications != null}{summary.cleared_notifications}
									cleared{/if}
							</span>
						{/if}
					{/if}
				</div>
				<svg
					class="h-4 w-4 transition-transform {notificationsOpen ? 'rotate-180' : ''}"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M19 9l-7 7-7-7"
					/>
				</svg>
			</button>
			{#if notificationsOpen}
				<div class="border-t border-primary/10 px-4 py-3 dark:border-primary/10">
					<div class="flex flex-wrap gap-2">
						<button
							onclick={handleDismissNotifications}
							disabled={busy || !summary?.unseen_notifications}
							class="rounded bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary-text transition-colors hover:bg-primary/20 disabled:opacity-50 dark:text-primary-text-dark"
						>
							Dismiss All Unseen{#if summary?.unseen_notifications}
								({summary.unseen_notifications}){/if}
						</button>
						<button
							onclick={handlePurgeNotifications}
							disabled={busy || !summary?.cleared_notifications}
							class="rounded bg-red-500/15 px-3 py-1.5 text-xs font-medium text-red-700 transition-colors hover:bg-red-500/25 disabled:opacity-50 dark:text-red-400"
						>
							Purge Cleared{#if summary?.cleared_notifications}
								({summary.cleared_notifications}){/if}
						</button>
					</div>
				</div>
			{/if}
		</div>

		<!-- Transcoder Jobs -->
		<div class="rounded-lg border border-primary/15 dark:border-primary/15">
			<button
				onclick={() => {
					transcoderOpen = !transcoderOpen;
				}}
				class="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-gray-900 transition-colors hover:bg-primary/5 dark:text-white dark:hover:bg-primary/10"
			>
				<div class="flex items-center gap-2">
					<svg class="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"
						/>
					</svg>
					Transcoder Jobs
					{#if summary?.stale_transcoder_jobs != null}
						<span
							class="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary-text dark:text-primary-text-dark"
							>{summary.stale_transcoder_jobs}</span
						>
					{:else if summary && summary.stale_transcoder_jobs === null}
						<span class="text-xs text-gray-400">unavailable</span>
					{/if}
				</div>
				<svg
					class="h-4 w-4 transition-transform {transcoderOpen ? 'rotate-180' : ''}"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M19 9l-7 7-7-7"
					/>
				</svg>
			</button>
			{#if transcoderOpen}
				<div class="border-t border-primary/10 px-4 py-3 dark:border-primary/10">
					<p class="mb-2 text-xs text-gray-500 dark:text-gray-400">
						Remove completed and failed transcoder jobs from the transcoder database.
					</p>
					<button
						onclick={handleCleanupTranscoder}
						disabled={busy || !summary?.stale_transcoder_jobs}
						class="rounded bg-red-500/15 px-3 py-1.5 text-xs font-medium text-red-700 transition-colors hover:bg-red-500/25 disabled:opacity-50 dark:text-red-400"
					>
						Clean Up{#if summary?.stale_transcoder_jobs}
							({summary.stale_transcoder_jobs} job{summary.stale_transcoder_jobs !== 1
								? 's'
								: ''}){/if}
					</button>
				</div>
			{/if}
		</div>
		<!-- Image Cache -->
		<div class="rounded-lg border border-primary/15 dark:border-primary/15">
			<button
				onclick={() => {
					imageCacheOpen = !imageCacheOpen;
					if (imageCacheOpen && !cacheStats) loadCacheStats();
				}}
				class="flex w-full items-center gap-3 p-4 text-left"
			>
				<svg class="h-5 w-5 text-primary-text dark:text-primary-text-dark" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v13.5A1.5 1.5 0 003.75 21z" />
				</svg>
				Image Cache
				{#if cacheStats}
					<span class="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary-text dark:text-primary-text-dark">
						{cacheStats.count} image{cacheStats.count !== 1 ? 's' : ''} &middot; {cacheStats.size_mb} MB
					</span>
				{/if}
				<svg class="ml-auto h-4 w-4 transition-transform {imageCacheOpen ? 'rotate-180' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
				</svg>
			</button>
			{#if imageCacheOpen}
				<div class="border-t border-primary/10 p-4 dark:border-primary/10">
					{#if cacheLoading}
						<p class="text-sm text-gray-500">Loading...</p>
					{:else if cacheStats}
						<p class="mb-3 text-sm text-gray-600 dark:text-gray-400">
							{cacheStats.count} cached poster image{cacheStats.count !== 1 ? 's' : ''}
							({cacheStats.size_mb} MB)
						</p>
						<button
							onclick={handleClearCache}
							disabled={busy || !cacheStats.count}
							class="rounded bg-red-500/15 px-3 py-1.5 text-xs font-medium text-red-700 transition-colors hover:bg-red-500/25 disabled:opacity-50 dark:text-red-400"
						>
							Clear Cache{#if cacheStats.count} ({cacheStats.count} image{cacheStats.count !== 1 ? 's' : ''}){/if}
						</button>
					{:else}
						<p class="text-sm text-gray-500">Unable to load cache stats</p>
					{/if}
				</div>
			{/if}
		</div>
	</div>
</div>

<!-- Confirm Dialog -->
{#if confirmOpen}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
		<div class="mx-4 max-w-sm rounded-lg bg-white p-5 shadow-xl dark:bg-gray-800">
			<h3 class="mb-2 font-semibold text-gray-900 dark:text-white">{confirmTitle}</h3>
			<p class="mb-4 text-sm text-gray-600 dark:text-gray-400">{confirmMessage}</p>
			<div class="flex justify-end gap-2">
				<button
					onclick={() => {
						confirmOpen = false;
						confirmAction = null;
					}}
					class="rounded px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
					>Cancel</button
				>
				<button
					onclick={executeConfirmed}
					class="rounded bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
					>Confirm</button
				>
			</div>
		</div>
	</div>
{/if}
