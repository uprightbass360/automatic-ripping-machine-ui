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

	// Unified theme: blue for ripper, cyan for transcoder
	const barColor = $derived(activePanel === 'ripper' ? 'bg-blue-500' : 'bg-cyan-500');
	function themedBar(percent: number): string {
		if (percent >= 90) return 'bg-red-500';
		if (percent >= 70) return 'bg-yellow-500';
		return barColor;
	}

	// Dynamic temperature color: green < 60, yellow 60–79, orange 80–89, red 90+
	function tempColor(deg: number): string {
		if (deg >= 90) return 'text-red-500';
		if (deg >= 80) return 'text-orange-500';
		if (deg >= 60) return 'text-yellow-500';
		return 'text-green-500';
	}

	// Round to nearest common memory size for display (2,4,6,8,12,16,24,32,48,64,128)
	const memSizes = [2, 4, 6, 8, 12, 16, 24, 32, 48, 64, 128];
	function niceMemSize(gb: number): number {
		for (const s of memSizes) {
			if (gb <= s) return s;
		}
		return Math.ceil(gb);
	}
</script>

<div
	data-stats
	class="border-t px-3 py-3 transition-colors duration-500
		{activePanel === 'ripper'
			? 'border-blue-500/20 bg-blue-500/[0.04]'
			: 'border-cyan-500/20 bg-cyan-500/[0.04]'}"
>
	<!-- Panel switcher — always visible -->
	<div class="mb-2 flex rounded-sm bg-primary/10 p-0.5 dark:bg-primary/10">
		<button
			onclick={() => activePanel = 'ripper'}
			class="flex-1 rounded-sm px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider transition-all duration-500
				{activePanel === 'ripper'
					? 'bg-blue-500/20 text-blue-400 shadow-[0_0_10px_rgba(59,130,246,0.25)]'
					: 'text-gray-500 hover:text-gray-300'}"
		>Ripper</button>
		<button
			onclick={() => activePanel = 'transcoder'}
			class="flex-1 rounded-sm px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider transition-all duration-500
				{activePanel === 'transcoder'
					? 'bg-cyan-500/20 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.3)]'
					: 'text-gray-500 hover:text-gray-300'}"
		>Transcoder</button>
	</div>

		<!-- Hardware specs for active panel -->
		{#if activePanel === 'ripper' && !armOnline}
			<p class="text-xs text-orange-500 dark:text-orange-400">Cannot reach the ARM ripping service</p>
		{:else if activePanel === 'transcoder' && !transcoderOnline}
			<p class="text-xs text-orange-500 dark:text-orange-400">Cannot reach the transcoder service</p>
		{:else if activeHw}
			{#if activePanel === 'transcoder' && activeHw.gpu_name}
				<p class="truncate text-[11px] text-cyan-500" title={activeHw.gpu_name}>{activeHw.gpu_name}</p>
			{:else}
				<p class="truncate text-[11px] text-blue-400" title={activeHw.cpu ?? undefined}>{activeHw.cpu ?? 'Unknown CPU'}</p>
			{/if}
			<p class="mb-2 text-xs text-gray-600 dark:text-gray-400">
				{#if activePanel === 'transcoder' && activeHw.gpu_vram_gb}
					{niceMemSize(activeHw.gpu_vram_gb)} GB VRAM
				{:else}
					{activeHw.memory_total_gb ? `${niceMemSize(activeHw.memory_total_gb)} GB RAM` : 'RAM: N/A'}
				{/if}
			</p>
		{/if}

		<!-- CPU / GPU & Memory -->
		{#if activeStats}
			<div class="space-y-2">
				<div>
					{#if activePanel === 'transcoder' && activeStats.gpu_percent !== undefined}
						<div class="mb-0.5 flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400">
							<span>GPU</span>
							<span class="whitespace-nowrap">
								{activeStats.gpu_percent}%
								{#if activeStats.gpu_temp > 0}
									<span class="{tempColor(activeStats.gpu_temp)}">&nbsp;{activeStats.gpu_temp.toFixed(0)}&deg;C</span>
								{/if}
							</span>
						</div>
						<ProgressBar
							value={activeStats.gpu_percent}
							color={themedBar(activeStats.gpu_percent)}
							showLabel={false}
						/>
					{:else}
						<div class="mb-0.5 flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400">
							<span>CPU</span>
							<span class="whitespace-nowrap">
								{activeStats.cpu_percent}%
								{#if activeStats.cpu_temp > 0}
									<span class="{tempColor(activeStats.cpu_temp)}">&nbsp;{activeStats.cpu_temp.toFixed(0)}&deg;C</span>
								{/if}
							</span>
						</div>
						<ProgressBar
							value={activeStats.cpu_percent}
							color={themedBar(activeStats.cpu_percent)}
							showLabel={false}
						/>
					{/if}
				</div>

				{#if activePanel === 'transcoder' && activeStats.gpu_memory}
					{@const mem = activeStats.gpu_memory}
					<div>
						<div class="mb-0.5 flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400">
							<span>Mem</span>
							<span>{mem.used_gb < 1 ? `${(mem.used_gb * 1024).toFixed(0)} MB` : `${mem.used_gb} GB`} / {niceMemSize(mem.total_gb)} GB</span>
						</div>
						<ProgressBar
							value={mem.percent}
							color={themedBar(mem.percent)}
							showLabel={false}
						/>
					</div>
				{:else if activeStats.memory}
					{@const mem = activeStats.memory}
					<div>
						<div class="mb-0.5 flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400">
							<span>Mem</span>
							<span>{mem.used_gb < 1 ? `${(mem.used_gb * 1024).toFixed(0)} MB` : `${mem.used_gb} GB`} / {niceMemSize(mem.total_gb)} GB</span>
						</div>
						<ProgressBar
							value={mem.percent}
							color={themedBar(mem.percent)}
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
								color={themedBar(sp.percent)}
								showLabel={false}
							/>
						</div>
					{/each}
				</div>
			{/if}
		{/if}
</div>
