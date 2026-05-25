<script lang="ts">
	import type { CatalogService, ChannelType, CatalogField } from '$lib/types/notifications';
	import SchemaField from '../SchemaField.svelte';
	import ServiceGlyph from '../ServiceGlyph.svelte';
	import LabelEnabledRow from './LabelEnabledRow.svelte';

	let {
		type,
		name = $bindable(),
		enabled = $bindable(),
		config = $bindable(),
		service,
		showLabelRow = true,
		preserveExisting = false
	}: {
		type: ChannelType;
		name: string;
		enabled: boolean;
		config: Record<string, unknown>;
		service: CatalogService | null;
		showLabelRow?: boolean;
		preserveExisting?: boolean;
	} = $props();

	const webhookFields: CatalogField[] = [
		{ key: 'url', label: 'Webhook URL', type: 'string', private: false, required: true },
		{ key: 'shared_secret', label: 'Shared Secret', type: 'string', private: true, required: false }
	];
	const bashFields: CatalogField[] = [
		{ key: 'script_path', label: 'Script Path', type: 'string', private: false, required: true }
	];

	const rawFields = $derived(
		type === 'apprise'
			? [...(service?.required_fields ?? []), ...(service?.advanced_fields ?? [])]
			: type === 'webhook'
				? webhookFields
				: bashFields
	);
	const fields = $derived(
		preserveExisting ? rawFields.map((f) => ({ ...f, required: false })) : rawFields
	);
</script>

<div class="space-y-4">
	{#if showLabelRow}
		<LabelEnabledRow bind:name bind:enabled />
	{/if}

	{#if fields.length}
		<div class="rounded-lg border border-primary/15 bg-page p-4 dark:border-primary/20 dark:bg-primary/5">
			<div class="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-primary">
				{#if type === 'apprise' && service}
					<ServiceGlyph id={service.id} name={service.name} size={18} />
					{service.name} configuration
					<span class="ml-1 font-mono text-[11px] normal-case tracking-normal text-gray-500">{service.url_scheme}://…</span>
				{:else if type === 'webhook'}Webhook configuration{:else}Bash script configuration{/if}
			</div>
			{#if preserveExisting}
				<p class="mb-3 text-xs text-gray-500 dark:text-gray-400">Re-enter credentials to change the destination. Leave blank to keep the current settings.</p>
			{/if}
			<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
				{#each fields as f (f.key)}
					<div class={f.key === 'url' || f.key === 'script_path' ? 'sm:col-span-2' : ''}>
						<SchemaField field={f} bind:value={config[f.key]} />
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>
