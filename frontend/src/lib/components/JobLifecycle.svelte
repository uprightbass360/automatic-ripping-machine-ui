<script lang="ts">
	import { deriveLifecycle, lifecycleColorVar } from '$lib/utils/job-lifecycle';
	import { Pause } from 'lucide-svelte';

	interface Props {
		status: string | null | undefined;
		sourceType: string | null | undefined;
		size?: 'sm' | 'md';
	}

	let { status, sourceType, size = 'md' }: Props = $props();

	let nodes = $derived(deriveLifecycle(status, sourceType));
</script>

{#if size === 'sm'}
	<!-- Compact horizontal segments for the dashboard JobCard.
	     Each segment is a colored bar; the active one pulses; failure
	     segments use the error theme token. No labels rendered. -->
	<div
		class="inline-flex items-center gap-0.5"
		role="img"
		aria-label="Job lifecycle"
		title={nodes.map((n) => `${n.label}: ${n.state}`).join(' · ')}
	>
		{#each nodes as node (node.id)}
			<span
				class="relative h-1.5 w-6 rounded-sm {node.state === 'active' ? 'lifecycle-pulse' : ''}"
				style="background: {lifecycleColorVar(node.state)}; opacity: {node.state === 'pending' ? 0.35 : 1}"
			>
				{#if node.state === 'paused'}
					<Pause
						class="absolute -top-1 left-1/2 h-2.5 w-2.5 -translate-x-1/2 text-[var(--color-status-waiting)]"
					/>
				{/if}
			</span>
		{/each}
	</div>
{:else}
	<!-- Detail-page sized: pills with labels and connector lines. -->
	<ol
		class="flex items-center gap-1.5 text-xs"
		role="list"
		aria-label="Job lifecycle"
	>
		{#each nodes as node, i (node.id)}
			<li class="flex items-center gap-1.5">
				<span
					class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-medium {node.state ===
					'active'
						? 'lifecycle-pulse'
						: ''}"
					style="background: {node.state === 'pending'
						? 'transparent'
						: lifecycleColorVar(node.state)}; color: {node.state === 'pending'
						? 'var(--color-status-pending, #9ca3af)'
						: 'white'}; border: 1px solid {lifecycleColorVar(node.state)}; opacity: {node.state ===
					'pending'
						? 0.55
						: 1}"
					title={`${node.label}: ${node.state}`}
				>
					{#if node.state === 'paused'}
						<Pause class="h-3 w-3" />
					{/if}
					{node.label}
				</span>
				{#if i < nodes.length - 1}
					<span
						class="inline-block h-px w-3"
						style="background: {lifecycleColorVar(
							node.state === 'completed' ? 'completed' : 'pending'
						)}"
						aria-hidden="true"
					></span>
				{/if}
			</li>
		{/each}
	</ol>
{/if}

<style>
	.lifecycle-pulse {
		animation: lifecyclePulse 1.4s ease-in-out infinite;
	}
	@keyframes lifecyclePulse {
		0%, 100% {
			filter: brightness(1);
		}
		50% {
			filter: brightness(1.3);
		}
	}
</style>
