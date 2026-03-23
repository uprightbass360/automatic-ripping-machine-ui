<script lang="ts">
	import type { HardwareInfo, SystemStats } from '$lib/types/arm';

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

	const activeStats = $derived(activePanel === 'ripper' ? (armOnline ? systemStats : null) : (transcoderOnline ? transcoderStats : null));
	const isOffline = $derived(activePanel === 'ripper' ? !armOnline : !transcoderOnline);
	const offlineMessage = $derived(activePanel === 'ripper' ? 'Cannot reach the ARM ripping service' : 'Cannot reach the transcoder service');

	function cpuColor(pct: number): string {
		return pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-yellow-500' : 'bg-cyan-500';
	}
	function memColor(pct: number): string {
		return pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-yellow-500' : 'bg-violet-500';
	}
	function storageColor(pct: number): string {
		return pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-yellow-500' : 'bg-emerald-500';
	}
</script>

<div class="fixed bottom-0 left-64 right-0 z-30 hidden h-10 items-center gap-3 border-t border-primary/20 bg-surface px-4 lg:flex xl:hidden dark:border-primary/20 dark:bg-surface-dark">
	<!-- Panel toggle -->
	<div class="flex shrink-0 rounded-sm bg-primary/10 p-0.5 dark:bg-primary/10">
		<button
			onclick={() => activePanel = 'ripper'}
			class="rounded-sm px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider transition-colors
				{activePanel === 'ripper'
					? 'bg-primary/20 text-primary-text shadow-xs dark:bg-primary/25 dark:text-primary-text-dark'
					: 'text-primary-text/50 hover:text-primary-text dark:text-primary-text-dark/50 dark:hover:text-primary-text-dark'}"
		>Ripper</button>
		<button
			onclick={() => activePanel = 'transcoder'}
			class="rounded-sm px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider transition-colors
				{activePanel === 'transcoder'
					? 'bg-primary/20 text-primary-text shadow-xs dark:bg-primary/25 dark:text-primary-text-dark'
					: 'text-primary-text/50 hover:text-primary-text dark:text-primary-text-dark/50 dark:hover:text-primary-text-dark'}"
		>Transcoder</button>
	</div>

	<div class="h-5 w-px shrink-0 bg-primary/15 dark:bg-primary/20"></div>

	{#if isOffline}
		<span class="text-xs text-orange-500 dark:text-orange-400">{offlineMessage}</span>
	{:else if activeStats}
		<!-- CPU -->
		<div class="flex items-center gap-2 text-[11px] text-gray-500 dark:text-gray-400">
			<span class="shrink-0">CPU</span>
			<div class="h-1 w-16 rounded-full bg-primary/15 dark:bg-primary/15">
				<div class="h-1 rounded-full transition-all duration-500 {cpuColor(activeStats.cpu_percent)}" style="width: {Math.min(100, activeStats.cpu_percent)}%"></div>
			</div>
			<span class="shrink-0">{activeStats.cpu_percent}%</span>
		</div>

		<div class="h-5 w-px shrink-0 bg-primary/15 dark:bg-primary/20"></div>

		<!-- Memory -->
		{#if activeStats.memory}
			<div class="flex items-center gap-2 text-[11px] text-gray-500 dark:text-gray-400">
				<span class="shrink-0">Mem</span>
				<div class="h-1 w-16 rounded-full bg-primary/15 dark:bg-primary/15">
					<div class="h-1 rounded-full transition-all duration-500 {memColor(activeStats.memory.percent)}" style="width: {Math.min(100, activeStats.memory.percent)}%"></div>
				</div>
				<span class="shrink-0 whitespace-nowrap">{activeStats.memory.used_gb} / {activeStats.memory.total_gb} GB</span>
			</div>

			<div class="h-5 w-px shrink-0 bg-primary/15 dark:bg-primary/20"></div>
		{/if}

		<!-- Storage -->
		{#if activeStats.storage?.length}
			<div class="flex items-center gap-3 overflow-hidden text-[11px] text-gray-500 dark:text-gray-400">
				{#each activeStats.storage as sp}
					<div class="flex shrink-0 items-center gap-1.5">
						<span class="text-gray-400 dark:text-gray-500">{sp.name}</span>
						<div class="h-1 w-12 rounded-full bg-primary/15 dark:bg-primary/15">
							<div class="h-1 rounded-full transition-all duration-500 {storageColor(sp.percent)}" style="width: {Math.min(100, sp.percent)}%"></div>
						</div>
						<span>{sp.free_gb} GB</span>
					</div>
				{/each}
			</div>
		{/if}
	{/if}
</div>
