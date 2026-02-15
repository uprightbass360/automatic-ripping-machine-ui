<script lang="ts">
	import { onMount } from 'svelte';
	import { createPollingStore } from '$lib/stores/polling';
	import { fetchDrives } from '$lib/api/drives';
	import type { Drive } from '$lib/types/arm';
	import DriveCard from '$lib/components/DriveCard.svelte';

	const drives = createPollingStore(fetchDrives, [] as Drive[], 10000);

	onMount(() => {
		drives.start();
		return () => drives.stop();
	});
</script>

<svelte:head>
	<title>Drives - ARM UI</title>
</svelte:head>

<div class="space-y-6">
	<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Optical Drives</h1>

	{#if $drives.error}
		<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
			{$drives.error}
		</div>
	{:else if ($drives).length === 0}
		<p class="py-8 text-center text-gray-400">No drives detected.</p>
	{:else}
		<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
			{#each $drives as drive (drive.drive_id)}
				<DriveCard {drive} onupdate={() => drives.refresh()} />
			{/each}
		</div>
	{/if}
</div>
