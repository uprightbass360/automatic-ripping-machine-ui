<script lang="ts">
	import type { Catalog, CatalogService } from '$lib/types/notifications';

	let { catalog, onpick }: { catalog: Catalog; onpick: (id: string) => void } = $props();

	let open = $state(false);
	let search = $state('');
	let highlighted = $state(0);
	let rootEl: HTMLDivElement | undefined = $state();

	const byId = $derived(new Map(catalog.services.map((s) => [s.id, s])));

	const featuredServices = $derived(
		catalog.featured.map((id) => byId.get(id)).filter((s): s is CatalogService => !!s)
	);

	// When searching, match across all services; otherwise show featured first.
	const options = $derived(
		search.trim()
			? catalog.services.filter((s) =>
					s.name.toLowerCase().includes(search.trim().toLowerCase())
				)
			: featuredServices
	);

	function choose(id: string) {
		onpick(id);
		open = false;
		search = '';
	}

	function toggle() {
		open = !open;
		if (open) {
			search = '';
			highlighted = 0;
		}
	}

	function onKeydown(e: KeyboardEvent) {
		if (!open) {
			if (e.key === 'Enter' || e.key === 'ArrowDown' || e.key === ' ') {
				e.preventDefault();
				toggle();
			}
			return;
		}
		if (e.key === 'Escape') {
			open = false;
		} else if (e.key === 'ArrowDown') {
			e.preventDefault();
			highlighted = Math.min(highlighted + 1, options.length - 1);
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			highlighted = Math.max(highlighted - 1, 0);
		} else if (e.key === 'Enter') {
			e.preventDefault();
			const opt = options[highlighted];
			if (opt) choose(opt.id);
		}
	}

	$effect(() => {
		if (!open) return;
		function onDocClick(ev: MouseEvent) {
			if (rootEl && !rootEl.contains(ev.target as Node)) open = false;
		}
		document.addEventListener('click', onDocClick, true);
		return () => document.removeEventListener('click', onDocClick, true);
	});

	// Keep the highlighted index in range as the filtered list changes.
	$effect(() => {
		if (highlighted > options.length - 1) highlighted = 0;
	});
</script>

<div class="relative" bind:this={rootEl}>
	<button
		type="button"
		onclick={toggle}
		onkeydown={onKeydown}
		aria-haspopup="listbox"
		aria-expanded={open}
		class="flex w-full items-center justify-between rounded-md border border-primary/25 bg-primary/5 px-3 py-2 text-left text-sm text-gray-700 hover:border-primary focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-gray-200"
	>
		<span>Select a service…</span>
		<svg
			class="h-4 w-4 transform transition-transform {open ? 'rotate-180' : ''}"
			fill="none" stroke="currentColor" viewBox="0 0 24 24"
		>
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
		</svg>
	</button>

	{#if open}
		<div
			class="absolute z-20 mt-1 w-full overflow-hidden rounded-md border border-primary/25 bg-surface shadow-lg dark:border-primary/30 dark:bg-surface-dark"
		>
			<div class="p-2">
				<!-- svelte-ignore a11y_autofocus -->
				<input
					type="search"
					placeholder="Search services"
					bind:value={search}
					onkeydown={onKeydown}
					autofocus
					class="w-full rounded-md border border-primary/25 bg-primary/5 px-3 py-2 text-sm focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white"
				/>
			</div>
			<ul role="listbox" class="max-h-60 overflow-y-auto py-1">
				{#if options.length === 0}
					<li class="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">No services match "{search}".</li>
				{:else}
					{#each options as svc, i (svc.id)}
						<li role="option" aria-selected={i === highlighted}>
							<button
								type="button"
								onclick={() => choose(svc.id)}
								onmouseenter={() => (highlighted = i)}
								class="block w-full px-3 py-2 text-left text-sm text-gray-800 hover:bg-primary/10 dark:text-gray-200 dark:hover:bg-primary/15 {i === highlighted ? 'bg-primary/10 dark:bg-primary/15' : ''}"
							>
								{svc.name}
							</button>
						</li>
					{/each}
				{/if}
			</ul>
			{#if !search.trim()}
				<p class="border-t border-primary/15 px-3 py-1.5 text-xs text-gray-500 dark:border-primary/20 dark:text-gray-400">
					Showing {featuredServices.length} featured — type to search all {catalog.services.length}.
				</p>
			{/if}
		</div>
	{/if}
</div>
