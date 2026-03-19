<script lang="ts">
	import type { SetupStatus } from '$lib/types/setup';
	import { onMount } from 'svelte';

	interface Props {
		status: SetupStatus;
	}

	let { status }: Props = $props();

	let systemInfo = $state<{ cpu: string; memory_total_gb: number } | null>(null);

	onMount(async () => {
		try {
			const resp = await fetch('/api/system-info');
			if (resp.ok) systemInfo = await resp.json();
		} catch { /* non-critical */ }
	});
</script>

<div class="space-y-6">
	<div class="text-center">
		<h2 class="text-2xl font-bold text-gray-900 dark:text-white">Welcome to ARM</h2>
		<p class="mt-2 text-gray-600 dark:text-gray-400">
			Let's make sure your system is configured correctly.
		</p>
	</div>

	<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
		<!-- ARM Version -->
		<div class="rounded-lg border border-primary/20 bg-surface p-4 dark:border-primary/20 dark:bg-surface-dark">
			<div class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">ARM Version</div>
			<div class="mt-1 text-lg font-medium text-gray-900 dark:text-white">{status.arm_version}</div>
		</div>

		<!-- Database -->
		<div class="rounded-lg border border-primary/20 bg-surface p-4 dark:border-primary/20 dark:bg-surface-dark">
			<div class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Database</div>
			<div class="mt-1 flex items-center gap-2">
				{#if status.db_initialized}
					<svg class="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
						<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
					</svg>
					<span class="text-lg font-medium text-green-600 dark:text-green-400">Initialized</span>
				{:else}
					<svg class="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
						<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
					</svg>
					<span class="text-lg font-medium text-red-600 dark:text-red-400">Not initialized</span>
				{/if}
			</div>
		</div>

		<!-- CPU -->
		{#if systemInfo}
			<div class="rounded-lg border border-primary/20 bg-surface p-4 dark:border-primary/20 dark:bg-surface-dark">
				<div class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">CPU</div>
				<div class="mt-1 truncate text-sm font-medium text-gray-900 dark:text-white" title={systemInfo.cpu}>
					{systemInfo.cpu}
				</div>
			</div>

			<div class="rounded-lg border border-primary/20 bg-surface p-4 dark:border-primary/20 dark:bg-surface-dark">
				<div class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Memory</div>
				<div class="mt-1 text-lg font-medium text-gray-900 dark:text-white">
					{systemInfo.memory_total_gb.toFixed(1)} GB
				</div>
			</div>
		{/if}
	</div>

	<!-- Transcoder status -->
	<div class="rounded-lg border border-primary/20 bg-surface p-4 dark:border-primary/20 dark:bg-surface-dark">
		<div class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Drives Detected</div>
		<div class="mt-1 text-sm text-gray-900 dark:text-white">{status.setup_steps.drives}</div>
	</div>
</div>
