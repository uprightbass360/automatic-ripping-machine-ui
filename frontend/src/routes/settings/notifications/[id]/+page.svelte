<script lang="ts">
	import { goto } from '$app/navigation';
	import EventSubscriptions from '$lib/components/notifications/EventSubscriptions.svelte';
	import TemplateEditor from '$lib/components/notifications/TemplateEditor.svelte';
	import DispatchHistory from '$lib/components/notifications/DispatchHistory.svelte';
	import { updateChannel, testSendChannel, fetchDispatch } from '$lib/api/channels';
	import type { Channel, ChannelTemplate, DispatchRow } from '$lib/types/notifications';

	let { data }: { data: { channel: Channel; dispatches: DispatchRow[] } } = $props();

	let name = $state(data.channel.name);
	let enabled = $state(data.channel.enabled);
	let subscribedEvents = $state<string[]>([...data.channel.subscribed_events]);
	let templates = $state<Record<string, ChannelTemplate>>({ ...data.channel.templates });

	let toast = $state<string | null>(null);
	let testing = $state(false);
	let saving = $state(false);

	async function save() {
		saving = true;
		toast = null;
		try {
			await updateChannel(data.channel.id, {
				name,
				enabled,
				subscribed_events: subscribedEvents,
				templates
			});
			toast = 'Saved.';
		} catch (e) {
			toast = e instanceof Error ? e.message : 'Save failed';
		} finally {
			saving = false;
		}
	}

	async function runTest() {
		testing = true;
		toast = null;
		try {
			const { dispatch_id } = await testSendChannel(data.channel.id, 'job.started');
			// Poll up to 5s (10 * 500ms).
			for (let i = 0; i < 10; i++) {
				await new Promise((r) => setTimeout(r, 500));
				const d = await fetchDispatch(dispatch_id);
				if (d.status === 'success') {
					toast = 'Test sent successfully';
					return;
				}
				if (d.status === 'failed') {
					toast = `Test failed: ${d.last_error ?? 'unknown'}`;
					return;
				}
			}
			toast = 'Send is still pending — check Recent sends.';
		} catch (e) {
			toast = e instanceof Error ? e.message : 'Test failed';
		} finally {
			testing = false;
		}
	}
</script>

<section class="channel-edit">
	<h1>Edit channel</h1>
	{#if toast}<p class="toast">{toast}</p>{/if}

	<label>Channel name <input aria-label="Channel name" bind:value={name} /></label>
	<label><input type="checkbox" bind:checked={enabled} /> Enabled</label>

	<EventSubscriptions bind:selected={subscribedEvents} />
	<details>
		<summary>Templates</summary>
		<TemplateEditor {subscribedEvents} bind:templates />
	</details>

	<div class="actions">
		<button type="button" disabled={testing} onclick={runTest}>Test</button>
		<button type="button" onclick={() => goto('/settings/notifications')}>Back</button>
		<button type="button" disabled={saving} onclick={save}>Save</button>
	</div>

	<DispatchHistory rows={data.dispatches} />
</section>
