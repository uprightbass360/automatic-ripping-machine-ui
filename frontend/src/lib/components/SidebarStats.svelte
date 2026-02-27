<script lang="ts">
	import type { HardwareInfo, SystemStats } from '$lib/types/arm';
	import ProgressBar from './ProgressBar.svelte';

	interface Props {
		systemInfo: HardwareInfo | null;
		systemStats: SystemStats | null;
		transcoderInfo?: HardwareInfo | null;
		transcoderStats?: SystemStats | null;
		armOnline?: boolean;
		transcoderOnline?: boolean;
	}

	let { systemInfo, systemStats, transcoderInfo = null, transcoderStats = null, armOnline = true, transcoderOnline = true }: Props = $props();

	type Panel = 'ripper' | 'transcoder';
	let activePanel = $state<Panel>('ripper');

	const activeHw = $derived(activePanel === 'ripper' ? (armOnline ? systemInfo : null) : (transcoderOnline ? transcoderInfo : null));
	const activeStats = $derived(activePanel === 'ripper' ? (armOnline ? systemStats : null) : (transcoderOnline ? transcoderStats : null));
</script>

<div data-stats class="border-t border-primary/20 px-3 py-3 dark:border-primary/20">
	<!-- Panel switcher — always visible -->
	<div class="mb-2 flex rounded-sm bg-primary/10 p-0.5 dark:bg-primary/10">
		<button
			onclick={() => activePanel = 'ripper'}
			class="flex-1 rounded-sm px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider transition-colors
				{activePanel === 'ripper'
					? 'bg-primary/20 text-primary-text shadow-xs dark:bg-primary/25 dark:text-primary-text-dark'
					: 'text-primary-text/50 hover:text-primary-text dark:text-primary-text-dark/50 dark:hover:text-primary-text-dark'}"
		>Ripper</button>
		<button
			onclick={() => activePanel = 'transcoder'}
			class="flex-1 rounded-sm px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider transition-colors
				{activePanel === 'transcoder'
					? 'bg-primary/20 text-primary-text shadow-xs dark:bg-primary/25 dark:text-primary-text-dark'
					: 'text-primary-text/50 hover:text-primary-text dark:text-primary-text-dark/50 dark:hover:text-primary-text-dark'}"
		>Transcoder</button>
	</div>

		<!-- Hardware specs for active panel -->
		{#if activePanel === 'ripper' && !armOnline}
			<p class="text-xs text-orange-500 dark:text-orange-400">Cannot reach the ARM ripping service</p>
		{:else if activePanel === 'transcoder' && !transcoderOnline}
			<p class="text-xs text-orange-500 dark:text-orange-400">Cannot reach the transcoder service</p>
		{:else if activeHw}
			<p class="truncate text-xs text-gray-600 dark:text-gray-400" title={activeHw.cpu ?? undefined}>{activeHw.cpu ?? 'Unknown CPU'}</p>
			<p class="mb-2 text-xs text-gray-600 dark:text-gray-400">
				{activeHw.memory_total_gb ? `${activeHw.memory_total_gb.toFixed(1)} GB RAM` : 'RAM: N/A'}
			</p>
		{/if}

		<!-- CPU & Memory -->
		{#if activeStats}
			<div class="space-y-2">
				<div>
					<div class="mb-0.5 flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400">
						<span>CPU</span>
						<span class="whitespace-nowrap">
							{activeStats.cpu_percent}%
							{#if activeStats.cpu_temp > 0}
								<span class="text-orange-500">&nbsp;{activeStats.cpu_temp.toFixed(0)}&deg;C</span>
							{/if}
						</span>
					</div>
					<ProgressBar
						value={activeStats.cpu_percent}
						color={activeStats.cpu_percent >= 90 ? 'bg-red-500' : activeStats.cpu_percent >= 70 ? 'bg-yellow-500' : 'bg-cyan-500'}
						showLabel={false}
					/>
				</div>

				{#if activeStats.memory}
					<div>
						<div class="mb-0.5 flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400">
							<span>Mem</span>
							<span>{activeStats.memory.used_gb} / {activeStats.memory.total_gb} GB</span>
						</div>
						<ProgressBar
							value={activeStats.memory.percent}
							color={activeStats.memory.percent >= 90 ? 'bg-red-500' : activeStats.memory.percent >= 70 ? 'bg-yellow-500' : 'bg-violet-500'}
							showLabel={false}
						/>
					</div>
				{/if}
			</div>

			<!-- Storage -->
			{#if activeStats.storage?.length}
				<div class="mt-3 space-y-2">
					<p class="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Storage</p>
					{#each activeStats.storage as sp}
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
</div>
