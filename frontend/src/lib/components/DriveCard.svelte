<script lang="ts">
	import type { Drive } from '$lib/types/arm';
	import { updateDrive, scanDrive, deleteDrive, ejectDrive } from '$lib/api/drives';
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
	let removing = $state(false);
	let ejecting = $state(false);
	let togglingMode = $state(false);

	let isStale = $derived(!drive.mount || drive.stale === true);

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

	async function handleRemove() {
		if (!confirm(`Remove "${drive.name || drive.mount || `Drive ${drive.drive_id}`}" from the database? This drive will reappear on the next rescan if it's still connected.`)) return;
		removing = true;
		try {
			await deleteDrive(drive.drive_id);
			onupdate?.();
		} catch {
			removing = false;
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

	async function handleEject(method: 'eject' | 'close') {
		ejecting = true;
		try {
			await ejectDrive(drive.drive_id, method);
		} catch {
			// ignore — tray action is best-effort
		} finally {
			ejecting = false;
		}
	}

	async function toggleMode() {
		togglingMode = true;
		const newMode = drive.drive_mode === 'manual' ? 'auto' : 'manual';
		try {
			await updateDrive(drive.drive_id, { drive_mode: newMode });
			onupdate?.();
		} catch {
			// ignore
		} finally {
			togglingMode = false;
		}
	}
</script>

<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark {isStale ? 'opacity-60' : ''}">
	<div class="mb-3 flex items-center justify-between">
		<div class="flex items-center gap-2">
			<h3 class="font-semibold text-gray-900 dark:text-white">
				{drive.name || drive.mount || `Drive ${drive.drive_id}`}
			</h3>
			{#if isStale}
				<span class="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-medium text-amber-700 dark:text-amber-400">Stale</span>
			{/if}
		</div>
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
			<span class="inline-flex items-center gap-1 rounded-sm bg-green-500/20 px-1.5 py-0.5 text-xs text-green-700 dark:text-green-400">
				<DiscTypeIcon disctype="music" size="h-3.5 w-3.5" />CD
			</span>
		{/if}
		{#if drive.read_dvd}
			<span class="inline-flex items-center gap-1 rounded-sm bg-primary/15 px-1.5 py-0.5 text-xs text-primary-text dark:text-primary-text-dark">
				<DiscTypeIcon disctype="dvd" size="h-3.5 w-3.5" />DVD
			</span>
		{/if}
		{#if drive.read_bd}
			<span class="inline-flex items-center gap-1 rounded-sm bg-purple-500/20 px-1.5 py-0.5 text-xs text-purple-700 dark:text-purple-400">
				<DiscTypeIcon disctype="bluray" size="h-3.5 w-3.5" />Blu-ray
			</span>
			<label
				class="inline-flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400"
				title="Display only — UHD disc detection and transcoding presets are applied automatically regardless of this setting."
			>
				<input
					type="checkbox"
					checked={drive.uhd_capable ?? false}
					disabled={togglingUhd}
					onchange={toggleUhd}
					class="h-3.5 w-3.5 rounded-sm border-gray-300 text-amber-600 focus:ring-amber-500 dark:border-gray-600 dark:bg-gray-700"
				/>
				UHD Capable
				<svg class="h-3.5 w-3.5 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
			</label>
		{/if}
	</div>

	<!-- Drive mode badge -->
	<div class="mt-3 flex items-center gap-2 border-t border-primary/15 pt-3 dark:border-primary/20">
		<button
			onclick={toggleMode}
			disabled={togglingMode}
			class="rounded-sm px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider transition-colors
				{drive.drive_mode === 'manual'
					? 'bg-amber-500/20 text-amber-700 hover:bg-amber-500/30 dark:text-amber-400'
					: 'bg-primary/10 text-primary-text hover:bg-primary/20 dark:text-primary-text-dark'}
				disabled:opacity-50"
			title="Toggle between auto and manual rip mode"
		>
			{drive.drive_mode === 'manual' ? 'Manual' : 'Auto'}
		</button>

		<div class="ml-auto flex items-center gap-1.5">
			<!-- Eject -->
			<button
				onclick={() => handleEject('eject')}
				disabled={ejecting}
				class="rounded-md p-1.5 text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-300 disabled:opacity-50 transition-colors"
				title="Eject tray"
			>
				<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7M5 19h14" />
				</svg>
			</button>
			<!-- Close tray -->
			<button
				onclick={() => handleEject('close')}
				disabled={ejecting}
				class="rounded-md p-1.5 text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-300 disabled:opacity-50 transition-colors"
				title="Close tray"
			>
				<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7M5 5h14" />
				</svg>
			</button>
		</div>
	</div>

	<div class="mt-2 flex items-center gap-2">
		<button
			onclick={handleScan}
			disabled={scanning || scanCooldown}
			class="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors
				{scanning ? 'bg-primary/30 text-primary-text dark:text-primary-text-dark' : 'bg-primary/15 text-primary-text hover:bg-primary/25 dark:text-primary-text-dark dark:hover:bg-primary/30'}
				disabled:opacity-50 disabled:cursor-not-allowed"
		>
			<svg class="h-4 w-4 {scanning ? 'animate-spin' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
			</svg>
			{scanning ? 'Scanning...' : scanCooldown ? 'Scan Sent' : 'Force Scan'}
		</button>
		{#if isStale && !drive.current_job}
			<button
				onclick={handleRemove}
				disabled={removing}
				class="rounded-lg px-3 py-1.5 text-sm font-medium text-red-700 bg-red-500/15 hover:bg-red-500/25 disabled:opacity-50 dark:text-red-400 dark:hover:bg-red-500/30 transition-colors"
			>
				{removing ? 'Removing...' : 'Remove'}
			</button>
		{/if}
		{#if drive.current_job}
			<a href="/jobs/{drive.current_job.job_id}" class="text-sm text-primary-text hover:underline dark:text-primary-text-dark">
				{drive.current_job.title || drive.current_job.label || 'Active Job'}
			</a>
		{/if}
	</div>
</div>
