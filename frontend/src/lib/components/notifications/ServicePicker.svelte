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

<div class="service-picker">
	<input
		type="search"
		placeholder="Search services"
		bind:value={search}
	/>

	<div class="service-picker__grid">
		{#each filtered as svc (svc.id)}
			<button type="button" class="service-picker__item" onclick={() => onpick(svc.id)}>
				{svc.name}
			</button>
		{/each}
	</div>

	{#if !search.trim() && !showAll}
		<button type="button" class="service-picker__more" onclick={() => (showAll = true)}>
			Show all ({catalog.services.length})
		</button>
	{/if}
</div>
