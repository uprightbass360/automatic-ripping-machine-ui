<script lang="ts">
	import type { DispatchRow } from '$lib/types/notifications';

	let { rows }: { rows: DispatchRow[] } = $props();

	function statusIcon(status: DispatchRow['status']): string {
		if (status === 'success') return '✓';
		if (status === 'failed') return '⚠';
		return '⏱';
	}
</script>

<div class="dispatch-history">
	<h4>Recent sends</h4>
	{#if rows.length === 0}
		<p class="dispatch-history__empty">No sends yet.</p>
	{:else}
		<ul>
			{#each rows as row (row.id)}
				<li>
					<span class="dispatch-history__icon">{statusIcon(row.status)}</span>
					<span class="dispatch-history__event">{row.event_key}</span>
					<span class="dispatch-history__time">{row.created_at ?? ''}</span>
					{#if row.last_error}
						<span class="dispatch-history__error">· {row.last_error}</span>
					{/if}
				</li>
			{/each}
		</ul>
	{/if}
</div>
