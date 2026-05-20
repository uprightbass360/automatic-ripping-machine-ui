<script lang="ts">
	import { goto } from '$app/navigation';
	import ServicePicker from '$lib/components/notifications/ServicePicker.svelte';
	import SchemaField from '$lib/components/notifications/SchemaField.svelte';
	import EventSubscriptions from '$lib/components/notifications/EventSubscriptions.svelte';
	import TemplateEditor from '$lib/components/notifications/TemplateEditor.svelte';
	import { composeUrl, createChannel } from '$lib/api/channels';
	import type { Catalog, CatalogService, ChannelTemplate } from '$lib/types/notifications';

	let { data }: { data: { catalog: Catalog } } = $props();

	type Step = 'type' | 'service' | 'form';
	let step = $state<Step>('type');
	let chanType = $state<'apprise' | 'webhook' | 'bash'>('apprise');

	let service = $state<CatalogService | null>(null);
	let requiredValues = $state<Record<string, unknown>>({});
	let advancedValues = $state<Record<string, unknown>>({});
	let rawUrl = $state('');

	let name = $state('');
	let enabled = $state(true);
	let subscribedEvents = $state<string[]>([]);
	let templates = $state<Record<string, ChannelTemplate>>({});

	// webhook
	let webhookUrl = $state('');
	let sharedSecret = $state('');
	let headersText = $state('');

	// bash
	let scriptPath = $state('');

	let error = $state<string | null>(null);
	let saving = $state(false);

	function next() {
		if (chanType === 'apprise') step = 'service';
		else step = 'form';
	}

	function pickService(id: string) {
		service = data.catalog.services.find((s) => s.id === id) ?? null;
		requiredValues = {};
		advancedValues = {};
		step = 'form';
	}

	function parseHeaders(text: string): Record<string, string> {
		const out: Record<string, string> = {};
		for (const line of text.split('\n')) {
			const idx = line.indexOf(':');
			if (idx > 0) {
				const k = line.slice(0, idx).trim();
				const v = line.slice(idx + 1).trim();
				if (k) out[k] = v;
			}
		}
		return out;
	}

	async function save() {
		error = null;
		saving = true;
		try {
			let config: Record<string, unknown>;
			if (chanType === 'apprise') {
				let url = rawUrl.trim();
				if (!url && service) {
					const composed = await composeUrl(service.id, requiredValues, advancedValues);
					url = composed.url;
				}
				config = { type: 'apprise', url };
			} else if (chanType === 'webhook') {
				config = {
					type: 'webhook',
					url: webhookUrl,
					shared_secret: sharedSecret || null,
					headers: headersText.trim() ? parseHeaders(headersText) : null
				};
			} else {
				config = { type: 'bash', script_path: scriptPath };
			}

			await createChannel({
				type: chanType,
				name,
				enabled,
				config,
				subscribed_events: subscribedEvents,
				templates
			} as never);
			await goto('/settings/notifications');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Save failed';
		} finally {
			saving = false;
		}
	}
</script>

<section class="channel-new">
	<h1>Add channel</h1>
	{#if error}<p class="error">{error}</p>{/if}

	{#if step === 'type'}
		<fieldset>
			<legend>Choose channel type</legend>
			<label><input type="radio" aria-label="Service (Apprise)" bind:group={chanType} value="apprise" /> Service (Apprise)</label>
			<label><input type="radio" aria-label="Webhook" bind:group={chanType} value="webhook" /> Webhook</label>
			<label><input type="radio" aria-label="Bash script" bind:group={chanType} value="bash" /> Bash script</label>
		</fieldset>
		<button type="button" onclick={next}>Next</button>
	{:else if step === 'service'}
		<ServicePicker catalog={data.catalog} onpick={pickService} />
	{:else}
		<label>Channel name <input aria-label="Channel name" bind:value={name} /></label>
		<label><input type="checkbox" bind:checked={enabled} /> Enabled</label>

		{#if chanType === 'apprise' && service}
			<h3>{service.name}{#if service.docs_url}<a href={service.docs_url} target="_blank" rel="noreferrer"> docs ↗</a>{/if}</h3>
			<h4>Required</h4>
			{#each service.required_fields as f (f.key)}
				<SchemaField field={f} bind:value={requiredValues[f.key]} />
			{/each}
			{#if service.advanced_fields.length}
				<details>
					<summary>Advanced</summary>
					{#each service.advanced_fields as f (f.key)}
						<SchemaField field={f} bind:value={advancedValues[f.key]} />
					{/each}
				</details>
			{/if}
			<details>
				<summary>Or paste a raw Apprise URL</summary>
				<input aria-label="Raw Apprise URL" bind:value={rawUrl} placeholder="discord://..." />
			</details>
		{:else if chanType === 'webhook'}
			<label>Webhook URL <input aria-label="Webhook URL" bind:value={webhookUrl} /></label>
			<label>Shared secret (optional, enables HMAC) <input type="password" aria-label="Shared secret" bind:value={sharedSecret} /></label>
			<label>Custom headers (one per line, Key: value) <textarea aria-label="Custom headers" bind:value={headersText}></textarea></label>
		{:else}
			<label>Script path <input aria-label="Script path" bind:value={scriptPath} /></label>
			<p>Job context is passed as ARM_* environment variables.</p>
		{/if}

		<EventSubscriptions bind:selected={subscribedEvents} />
		<details>
			<summary>Templates</summary>
			<TemplateEditor subscribedEvents={subscribedEvents} bind:templates />
		</details>

		<div class="actions">
			<button type="button" onclick={() => goto('/settings/notifications')}>Cancel</button>
			<button type="button" disabled={saving} onclick={save}>Save</button>
		</div>
	{/if}
</section>
