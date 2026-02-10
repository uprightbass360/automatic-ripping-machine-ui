<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchSettings } from '$lib/api/settings';
	import type { SettingsData } from '$lib/types/arm';

	let settings = $state<SettingsData | null>(null);
	let error = $state<string | null>(null);

	onMount(async () => {
		try {
			settings = await fetchSettings();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load settings';
		}
	});
</script>

<svelte:head>
	<title>Settings - ARM UI</title>
</svelte:head>

<div class="space-y-6">
	<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>

	{#if error}
		<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
			{error}
		</div>
	{:else if !settings}
		<div class="py-8 text-center text-gray-400">Loading...</div>
	{:else}
		<!-- ARM Config -->
		<section>
			<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">ARM Configuration</h2>
			{#if settings.arm_config}
				<div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
					<table class="w-full text-left text-sm">
						<thead class="bg-gray-50 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
							<tr>
								<th class="px-4 py-3 font-medium">Setting</th>
								<th class="px-4 py-3 font-medium">Value</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
							{#each Object.entries(settings.arm_config) as [key, value]}
								<tr class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
									<td class="px-4 py-2 font-mono text-xs font-medium text-gray-500 dark:text-gray-400">{key}</td>
									<td class="px-4 py-2 text-gray-900 dark:text-white">
										{#if value === '***'}
											<span class="text-gray-400">*****</span>
										{:else}
											{value ?? ''}
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<p class="text-sm text-gray-400">No ARM configuration found.</p>
			{/if}
		</section>

		<!-- Transcoder Config -->
		<section>
			<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Transcoder Configuration</h2>
			{#if settings.transcoder_config}
				<div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
					<table class="w-full text-left text-sm">
						<thead class="bg-gray-50 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
							<tr>
								<th class="px-4 py-3 font-medium">Setting</th>
								<th class="px-4 py-3 font-medium">Value</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
							{#each Object.entries(settings.transcoder_config) as [key, value]}
								<tr class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
									<td class="px-4 py-2 font-mono text-xs font-medium text-gray-500 dark:text-gray-400">{key}</td>
									<td class="px-4 py-2 text-gray-900 dark:text-white">{typeof value === 'object' ? JSON.stringify(value) : value}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else}
				<p class="text-sm text-gray-400">Transcoder offline or no configuration available.</p>
			{/if}
		</section>
	{/if}
</div>
