<script lang="ts">
	import type { Drive } from '$lib/types/arm';
	import { updateDrive, scanDrive } from '$lib/api/drives';
	import StatusBadge from './StatusBadge.svelte';
	import DiscTypeIcon from './DiscTypeIcon.svelte';

	interface Props {
		drive: Drive;
		onupdate?: () => void;
	}

	let { drive, onupdate }: Props = $props();

	let editing = $state(false);
	let editName = $state('');
	let saving = $state(false);
	let togglingUhd = $state(false);
	let scanning = $state(false);
	let scanCooldown = $state(false);

	async function handleScan() {
		if (scanning || scanCooldown) return;
		scanning = true;
		try {
			await scanDrive(drive.drive_id);
		} catch {
			// ignore — scan is fire-and-forget
		} finally {
			scanning = false;
			scanCooldown = true;
			setTimeout(() => (scanCooldown = false), 10000);
		}
	}

	function startEdit() {
		editName = drive.name || '';
		editing = true;
	}

	function cancelEdit() {
		editing = false;
	}

	async function saveEdit() {
		saving = true;
		try {
			await updateDrive(drive.drive_id, { name: editName });
			editing = false;
			onupdate?.();
		} catch {
			// keep edit mode open on failure
		} finally {
			saving = false;
		}
	}

	async function toggleUhd() {
		togglingUhd = true;
		try {
			await updateDrive(drive.drive_id, { uhd_capable: !drive.uhd_capable });
			onupdate?.();
		} catch {
			// ignore
		} finally {
			togglingUhd = false;
		}
	}

	function onKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') saveEdit();
		if (e.key === 'Escape') cancelEdit();
	}
</script>

<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
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
	<div class="mb-3">
		{#if editing}
			<div class="flex items-center gap-2">
				<input
					type="text"
					bind:value={editName}
					onkeydown={onKeydown}
					class="rounded-sm border border-primary/25 bg-primary/5 px-2 py-1 text-sm font-semibold text-gray-900 dark:border-primary/30 dark:bg-primary/10 dark:text-white"
					disabled={saving}
				/>
				<button
					onclick={saveEdit}
					disabled={saving}
					class="rounded-sm bg-primary px-2 py-1 text-xs text-on-primary hover:bg-primary-hover disabled:opacity-50"
				>Save</button>
				<button
					onclick={cancelEdit}
					disabled={saving}
					class="rounded-sm px-2 py-1 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
				>Cancel</button>
			</div>
		{:else}
			<button
				onclick={startEdit}
				class="rounded-md px-2 py-1 text-xs font-medium text-gray-700 ring-1 ring-primary/25 hover:bg-primary/10 dark:text-gray-200 dark:ring-primary/30 dark:hover:bg-primary/15"
			>Change Name</button>
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
			<span class="inline-flex items-center gap-1 rounded-sm bg-green-100 px-1.5 py-0.5 text-xs text-green-700 dark:bg-green-900/30 dark:text-green-400">
				<DiscTypeIcon disctype="music" size="h-3.5 w-3.5" />CD
			</span>
		{/if}
		{#if drive.read_dvd}
			<span class="inline-flex items-center gap-1 rounded-sm bg-primary-light-bg px-1.5 py-0.5 text-xs text-primary-text dark:bg-primary-light-bg-dark/30 dark:text-primary-text-dark">
				<DiscTypeIcon disctype="dvd" size="h-3.5 w-3.5" />DVD
			</span>
		{/if}
		{#if drive.read_bd}
			<span class="inline-flex items-center gap-1 rounded-sm bg-purple-100 px-1.5 py-0.5 text-xs text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
				<DiscTypeIcon disctype="bluray" size="h-3.5 w-3.5" />Blu-ray
			</span>
			<label class="inline-flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
				<input
					type="checkbox"
					checked={drive.uhd_capable ?? false}
					disabled={togglingUhd}
					onchange={toggleUhd}
					class="h-3.5 w-3.5 rounded-sm border-gray-300 text-amber-600 focus:ring-amber-500 dark:border-gray-600 dark:bg-gray-700"
				/>
				UHD Capable
			</label>
		{/if}
	</div>

	<div class="mt-3 flex items-center gap-2 border-t border-primary/15 pt-3 dark:border-primary/20">
		<button
			onclick={handleScan}
			disabled={scanning || scanCooldown}
			class="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors
				{scanning ? 'bg-blue-200 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300' : 'bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:hover:bg-blue-900/50'}
				disabled:opacity-50 disabled:cursor-not-allowed"
		>
			<svg class="h-4 w-4 {scanning ? 'animate-spin' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
			</svg>
			{scanning ? 'Scanning...' : scanCooldown ? 'Scan Sent' : 'Force Scan'}
		</button>
		{#if drive.current_job}
			<a href="/jobs/{drive.current_job.job_id}" class="text-sm text-primary-text hover:underline dark:text-primary-text-dark">
				{drive.current_job.title || drive.current_job.label || 'Active Job'}
			</a>
		{/if}
	</div>
</div>
