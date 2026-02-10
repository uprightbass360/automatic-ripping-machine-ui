<script lang="ts">
	interface Props {
		value: number;
		max?: number;
		color?: string;
		showLabel?: boolean;
	}

	let { value, max = 100, color = 'bg-blue-500', showLabel = true }: Props = $props();
	let pct = $derived(Math.min(100, Math.max(0, (value / max) * 100)));
</script>

<div class="flex items-center gap-2">
	<div class="h-2.5 flex-1 rounded-full bg-gray-200 dark:bg-gray-700">
		<div
			class="h-2.5 rounded-full transition-all duration-500 {color}"
			style="width: {pct}%"
		></div>
	</div>
	{#if showLabel}
		<span class="min-w-[3ch] text-right text-xs text-gray-500 dark:text-gray-400">
			{Math.round(pct)}%
		</span>
	{/if}
</div>
