<script lang="ts">
	import type { Channel } from '$lib/types/notifications';

	let {
		channel,
		ontest,
		ondelete
	}: { channel: Channel; ontest: (id: number) => void; ondelete: (id: number) => void } = $props();

	const statusClass = $derived(
		!channel.enabled ? 'status-dot--disabled' : channel.last_error ? 'status-dot--error' : 'status-dot--healthy'
	);
</script>

<div class="channel-card">
	<span class="status-dot {statusClass}"></span>
	<div class="channel-card__main">
		<strong>{channel.name}</strong>
		<span class="channel-card__type">{channel.type}{channel.enabled ? '' : ' · disabled'}</span>
		{#if channel.last_error}
			<span class="channel-card__error">⚠ {channel.last_error}</span>
		{/if}
		<span class="channel-card__events">Events: {channel.subscribed_events.join(', ')}</span>
	</div>
	<div class="channel-card__actions">
		<button type="button" onclick={() => ontest(channel.id)}>Test</button>
		<a href={`/settings/notifications/${channel.id}`}>Edit</a>
		<button type="button" class="channel-card__delete" onclick={() => ondelete(channel.id)}>Delete</button>
	</div>
</div>
