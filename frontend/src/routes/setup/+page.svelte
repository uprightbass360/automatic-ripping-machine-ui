<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { fetchSetupStatus } from '$lib/api/setup';
	import type { SetupStatus } from '$lib/types/setup';
	import SetupWizard from '$lib/components/setup/SetupWizard.svelte';

	let status = $state<SetupStatus | null>(null);
	let error = $state<string | null>(null);

	onMount(async () => {
		try {
			status = await fetchSetupStatus();
			// If setup is already complete, redirect to dashboard
			if (status && status.db_initialized && status.db_current && !status.first_run) {
				goto('/');
				return;
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load setup status';
		}
	});
</script>

<svelte:head>
	<title>ARM - Setup</title>
</svelte:head>

<div class="min-h-screen bg-page dark:bg-page-dark">
	{#if error}
		<div class="flex min-h-screen items-center justify-center">
			<div class="rounded-lg border border-red-200 bg-red-50 p-6 text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
				{error}
			</div>
		</div>
	{:else if status}
		<SetupWizard {status} />
	{:else}
		<div class="flex min-h-screen items-center justify-center">
			<div class="text-gray-400">Loading...</div>
		</div>
	{/if}
</div>
