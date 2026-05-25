<script lang="ts">
	import type { Channel, Catalog, CatalogService, ChannelTemplate } from '$lib/types/notifications';
	import ConfigureSection from './sections/ConfigureSection.svelte';
	import EventsSection from './sections/EventsSection.svelte';
	import TemplatesSection from './sections/TemplatesSection.svelte';

	export interface EditorBody {
		name: string;
		enabled: boolean;
		config: Record<string, unknown>;
		subscribed_events: string[];
		templates: Record<string, ChannelTemplate>;
	}

	let {
		channel,
		catalog,
		onsave,
		ontest,
		onclose,
		ondelete
	}: {
		channel: Channel;
		catalog: Catalog;
		onsave: (body: EditorBody) => void;
		ontest: (body: EditorBody) => void;
		onclose: () => void;
		ondelete: () => void;
	} = $props();

	let name = $state(channel.name);
	let enabled = $state(channel.enabled);
	let config = $state<Record<string, unknown>>({ ...channel.config });
	let events = $state<string[]>([...channel.subscribed_events]);
	let templates = $state<Record<string, ChannelTemplate>>({ ...channel.templates });

	// Apprise service lookup is best-effort (config carries a composed url, not an id);
	// fall back to null so ConfigureSection renders generic fields.
	const service = $derived<CatalogService | null>(null);

	const dirty = $derived(
		name !== channel.name ||
		enabled !== channel.enabled ||
		JSON.stringify(config) !== JSON.stringify(channel.config) ||
		JSON.stringify(events) !== JSON.stringify(channel.subscribed_events) ||
		JSON.stringify(templates) !== JSON.stringify(channel.templates)
	);

	function body(): EditorBody {
		return { name, enabled, config, subscribed_events: events, templates };
	}
</script>

<div class="space-y-4 border-t border-primary/20 px-4 py-4 dark:border-primary/20">
	<ConfigureSection type={channel.type} bind:name bind:enabled bind:config {service} />
	<EventsSection bind:selected={events} />
	<TemplatesSection subscribedEvents={events} bind:templates />

	<div class="flex flex-wrap items-center gap-2">
		<button type="button" disabled={!dirty} onclick={() => onsave(body())} class="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-on-primary hover:bg-primary-hover disabled:opacity-40">Save changes</button>
		<button type="button" onclick={() => ontest(body())} class="rounded-md border border-primary/25 px-4 py-2 text-sm text-primary-text hover:bg-primary/10 dark:border-primary/30 dark:text-primary-text-dark">Send test</button>
		<button type="button" onclick={onclose} class="rounded-md px-4 py-2 text-sm text-gray-600 hover:bg-primary/10 dark:text-gray-300">Close</button>
		<button type="button" onclick={ondelete} class="ml-auto rounded-md border border-red-300 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 dark:border-red-500/40 dark:text-red-400 dark:hover:bg-red-900/20">Delete</button>
	</div>
</div>
