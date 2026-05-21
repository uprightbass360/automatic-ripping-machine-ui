<script lang="ts">
	import type { Catalog, CatalogService } from '$lib/types/notifications';

	let { catalog, onpick }: { catalog: Catalog; onpick: (id: string) => void } = $props();

	let search = $state('');
	let showAll = $state(false);

	const byId = $derived(new Map(catalog.services.map((s) => [s.id, s])));

	const featuredServices = $derived(
		catalog.featured.map((id) => byId.get(id)).filter((s): s is CatalogService => !!s)
	);

	const filtered = $derived(
		search.trim()
			? catalog.services.filter((s) => s.name.toLowerCase().includes(search.trim().toLowerCase()))
			: showAll
				? catalog.services
				: featuredServices
	);
</script>

<div class="space-y-3">
	<input
		type="search"
		placeholder="Search services"
		bind:value={search}
		class="w-full rounded-md border border-primary/25 bg-primary/5 px-3 py-2 text-sm focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white"
	/>

	{#if filtered.length === 0}
		<p class="text-sm text-gray-500 dark:text-gray-400">No services match "{search}".</p>
	{:else}
		<div class="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
			{#each filtered as svc (svc.id)}
				<button
					type="button"
					onclick={() => onpick(svc.id)}
					class="rounded-md border border-primary/25 bg-surface px-3 py-2 text-sm text-gray-800 hover:border-primary hover:bg-primary/10 dark:border-primary/30 dark:bg-surface-dark dark:text-gray-200 dark:hover:bg-primary/15"
				>
					{svc.name}
				</button>
			{/each}
		</div>
	{/if}

	{#if !search.trim() && !showAll}
		<button
			type="button"
			onclick={() => (showAll = true)}
			class="text-sm font-medium text-primary hover:text-primary-hover hover:underline"
		>
			Show all ({catalog.services.length})
		</button>
	{:else if !search.trim() && showAll}
		<button
			type="button"
			onclick={() => (showAll = false)}
			class="text-sm font-medium text-primary hover:text-primary-hover hover:underline"
		>
			Show featured only
		</button>
	{/if}
</div>
