<script lang="ts">
	import type { HardwareInfo, SystemStats } from '$lib/types/arm';
	import ProgressBar from './ProgressBar.svelte';

	interface Props {
		systemInfo: HardwareInfo | null;
		systemStats: SystemStats | null;
		transcoderInfo?: HardwareInfo | null;
	}

	let { systemInfo, systemStats, transcoderInfo = null }: Props = $props();

	const hasTranscoder = $derived(transcoderInfo?.cpu != null);

	type Panel = 'ripper' | 'transcoder';
	let activePanel = $state<Panel>('ripper');

	const activeHw = $derived(activePanel === 'ripper' ? systemInfo : transcoderInfo);
</script>

<div class="border-t border-primary/20 px-3 py-3 dark:border-primary/20">
	{#if !systemInfo && !systemStats}
		<p class="text-xs text-gray-400 dark:text-gray-500">Loading system info...</p>
	{:else}
		<!-- Panel switcher -->
		{#if hasTranscoder}
			<div class="mb-2 flex rounded bg-primary/10 p-0.5 dark:bg-primary/10">
				<button
					onclick={() => activePanel = 'ripper'}
					class="flex-1 rounded px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider transition-colors
						{activePanel === 'ripper'
							? 'bg-primary/20 text-primary-text shadow-sm dark:bg-primary/25 dark:text-primary-text-dark'
							: 'text-primary-text/50 hover:text-primary-text dark:text-primary-text-dark/50 dark:hover:text-primary-text-dark'}"
				>Ripper</button>
				<button
					onclick={() => activePanel = 'transcoder'}
					class="flex-1 rounded px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider transition-colors
						{activePanel === 'transcoder'
							? 'bg-primary/20 text-primary-text shadow-sm dark:bg-primary/25 dark:text-primary-text-dark'
							: 'text-primary-text/50 hover:text-primary-text dark:text-primary-text-dark/50 dark:hover:text-primary-text-dark'}"
				>Transcoder</button>
			</div>
		{:else}
			<p class="mb-0.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Hardware</p>
		{/if}

		<!-- Hardware specs for active panel -->
		{#if activeHw}
			<p class="truncate text-xs text-gray-600 dark:text-gray-400" title={activeHw.cpu ?? undefined}>{activeHw.cpu ?? 'Unknown CPU'}</p>
			<p class="mb-2 text-xs text-gray-600 dark:text-gray-400">
				{activeHw.memory_total_gb ? `${activeHw.memory_total_gb.toFixed(1)} GB RAM` : 'RAM: N/A'}
			</p>
		{/if}

		<!-- CPU & Memory -->
		{#if systemStats}
			<div class="space-y-2">
				<div>
					<div class="mb-0.5 flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400">
						<span>CPU</span>
						<span class="whitespace-nowrap">
							{systemStats.cpu_percent}%
							{#if systemStats.cpu_temp > 0}
								<span class="text-orange-500">&nbsp;{systemStats.cpu_temp.toFixed(0)}&deg;C</span>
							{/if}
						</span>
					</div>
					<ProgressBar
						value={systemStats.cpu_percent}
						color={systemStats.cpu_percent >= 90 ? 'bg-red-500' : systemStats.cpu_percent >= 70 ? 'bg-yellow-500' : 'bg-cyan-500'}
						showLabel={false}
					/>
				</div>

				{#if systemStats.memory}
					<div>
						<div class="mb-0.5 flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400">
							<span>Mem</span>
							<span>{systemStats.memory.used_gb} / {systemStats.memory.total_gb} GB</span>
						</div>
						<ProgressBar
							value={systemStats.memory.percent}
							color={systemStats.memory.percent >= 90 ? 'bg-red-500' : systemStats.memory.percent >= 70 ? 'bg-yellow-500' : 'bg-violet-500'}
							showLabel={false}
						/>
					</div>
				{/if}
			</div>

			<!-- Storage -->
			{#if systemStats.storage?.length}
				<div class="mt-3 space-y-2">
					<p class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Storage</p>
					{#each systemStats.storage as sp}
						<div>
							<div class="mb-0.5 flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400">
								<span>{sp.name}</span>
								<span>{sp.free_gb} GB free</span>
							</div>
							<ProgressBar
								value={sp.percent}
								color={sp.percent >= 90 ? 'bg-red-500' : sp.percent >= 70 ? 'bg-yellow-500' : 'bg-emerald-500'}
								showLabel={false}
							/>
						</div>
					{/each}
				</div>
			{/if}
		{/if}
	{/if}
</div>
