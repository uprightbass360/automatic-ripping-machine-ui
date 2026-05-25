<script lang="ts">
	import type { CatalogService, ChannelType, CatalogField } from '$lib/types/notifications';
	import { FIELD_INPUT_CLASS } from '$lib/types/notifications';
	import SchemaField from '../SchemaField.svelte';
	import ServiceGlyph from '../ServiceGlyph.svelte';
	import Toggle from '../Toggle.svelte';

	let {
		type,
		name = $bindable(),
		enabled = $bindable(),
		config = $bindable(),
		service
	}: {
		type: ChannelType;
		name: string;
		enabled: boolean;
		config: Record<string, unknown>;
		service: CatalogService | null;
	} = $props();

	const webhookFields: CatalogField[] = [
		{ key: 'url', label: 'Webhook URL', type: 'string', private: false, required: true },
		{ key: 'shared_secret', label: 'Shared Secret', type: 'string', private: true, required: false }
	];
	const bashFields: CatalogField[] = [
		{ key: 'script_path', label: 'Script Path', type: 'string', private: false, required: true }
	];

	const fields = $derived(
		type === 'apprise'
			? [...(service?.required_fields ?? []), ...(service?.advanced_fields ?? [])]
			: type === 'webhook'
				? webhookFields
				: bashFields
	);
</script>

<div class="space-y-4">
	<div class="grid grid-cols-[1fr_auto] items-end gap-4">
		<label class="flex flex-col gap-1">
			<span class="text-sm font-medium text-gray-700 dark:text-gray-300">Channel Label *</span>
			<input class={FIELD_INPUT_CLASS} aria-label="Channel Label" bind:value={name} required />
		</label>
		<div class="flex items-center gap-2 pb-2">
			<Toggle checked={enabled} label="Enabled" onchange={(v) => (enabled = v)} />
			<span class="text-sm text-gray-700 dark:text-gray-300">Enabled</span>
		</div>
	</div>

	{#if fields.length}
		<div class="rounded-lg border border-primary/15 bg-page p-4 dark:border-primary/20 dark:bg-primary/5">
			<div class="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-primary">
				{#if type === 'apprise' && service}
					<ServiceGlyph id={service.id} name={service.name} size={18} />
					{service.name} configuration
					<span class="ml-1 font-mono text-[11px] normal-case tracking-normal text-gray-500">{service.url_scheme}://…</span>
				{:else if type === 'webhook'}Webhook configuration{:else}Bash script configuration{/if}
			</div>
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
