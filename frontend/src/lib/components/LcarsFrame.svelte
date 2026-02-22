<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		variant?: 'full' | 'compact';
		accent?: string;
		label?: string;
		children: Snippet;
	}

	let { variant = 'full', accent = '#f90', label = '', children }: Props = $props();
</script>

<div class="lcars-frame" data-lcars-variant={variant} style:--lcars-accent={accent}>
	<div class="lcars-bar lcars-bar-top" aria-hidden="true">
		{#if label}<span>{label}</span>{/if}
	</div>
	{#if variant === 'full'}
		<div class="lcars-sidebar" aria-hidden="true">
			<div class="lcars-block lcars-block-a"></div>
			<div class="lcars-block lcars-block-b"></div>
			<div class="lcars-block lcars-block-c"></div>
		</div>
	{/if}
	<div class="lcars-body">
		{@render children()}
	</div>
	<div class="lcars-bar lcars-bar-bottom" aria-hidden="true"></div>
</div>
