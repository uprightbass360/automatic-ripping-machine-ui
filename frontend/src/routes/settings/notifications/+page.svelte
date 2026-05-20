<script lang="ts">
	import ChannelCard from '$lib/components/notifications/ChannelCard.svelte';
	import { deleteChannel, testSendChannel } from '$lib/api/channels';
	import { invalidateAll } from '$app/navigation';
	import type { Channel } from '$lib/types/notifications';

	let { data }: { data: { channels: Channel[] } } = $props();

	let toast = $state<string | null>(null);

	async function onTest(id: number) {
		try {
			await testSendChannel(id, 'job.started');
			toast = 'Test queued — check Recent sends on the channel.';
		} catch (e) {
			toast = e instanceof Error ? e.message : 'Test failed';
		}
	}

	async function onDelete(id: number) {
		if (!confirm('Delete this channel? This cannot be undone.')) return;
		try {
			await deleteChannel(id);
			await invalidateAll();
		} catch (e) {
			toast = e instanceof Error ? e.message : 'Delete failed';
		}
	}
</script>

<section class="notifications-list">
	<header>
		<h1>Notifications</h1>
		<a class="btn" href="/settings/notifications/new">Add channel</a>
	</header>

	{#if toast}
		<p class="toast">{toast}</p>
	{/if}

	{#if data.channels.length === 0}
		<p class="empty">No notification channels yet.</p>
	{:else}
		{#each data.channels as channel (channel.id)}
			<ChannelCard {channel} ontest={onTest} ondelete={onDelete} />
		{/each}
	{/if}
</section>
