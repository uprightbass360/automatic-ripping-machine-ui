<script lang="ts">
	import type { Drive } from '$lib/types/arm';
	import { updateDrive } from '$lib/api/drives';
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
			<div class="flex items-center gap-1.5">
				<h3 class="font-semibold text-gray-900 dark:text-white">
					{drive.name || drive.mount || `Drive ${drive.drive_id}`}
				</h3>
				<button
					onclick={startEdit}
					class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
					title="Edit drive name"
				>
					<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
					</svg>
				</button>
			</div>
		{/if}
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

	{#if drive.current_job}
		<div class="mt-3 border-t border-primary/15 pt-3 dark:border-primary/20">
			<a href="/jobs/{drive.current_job.job_id}" class="text-sm text-primary-text hover:underline dark:text-primary-text-dark">
				{drive.current_job.title || drive.current_job.label || 'Active Job'}
			</a>
		</div>
	{/if}
</div>
