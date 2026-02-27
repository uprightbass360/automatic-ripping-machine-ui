<script lang="ts">
	import type { Job, MusicSearchResult, MusicDetail, TitleUpdate } from '$lib/types/arm';
	import { searchMusicMetadata, fetchMusicDetail, updateJobTitle } from '$lib/api/jobs';

	interface Props {
		job: Job;
		onapply?: () => void;
	}

	let { job, onapply }: Props = $props();

	let query = $state(job.title || job.label || '');
	let artistInput = $state('');
	let filterType = $state('');
	let filterFormat = $state('');
	let filterCountry = $state('');
	let filterStatus = $state('');
	let searching = $state(false);
	let results = $state<MusicSearchResult[]>([]);
	let searchError = $state<string | null>(null);

	let selectedId = $state<string | null>(null);
	let detail = $state<MusicDetail | null>(null);
	let loadingDetail = $state(false);

	let applying = $state(false);
	let feedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);

	// Editable metadata fields (populated from detail)
	let editTitle = $state('');
	let editYear = $state('');
	let editPosterUrl = $state('');

	$effect(() => {
		if (detail) {
			editTitle = detail.artist ? `${detail.artist} - ${detail.title}` : detail.title;
			editYear = detail.year;
			editPosterUrl = detail.poster_url ?? '';
		}
	});

	async function handleSearch() {
		if (!query.trim()) return;
		searching = true;
		searchError = null;
		results = [];
		selectedId = null;
		detail = null;
		try {
			results = await searchMusicMetadata(query.trim(), {
				artist: artistInput.trim() || undefined,
				release_type: filterType || undefined,
				format: filterFormat || undefined,
				country: filterCountry.trim() || undefined,
				status: filterStatus || undefined,
			});
			if (results.length === 0) {
				searchError = 'No results found. Try a different search term.';
			}
		} catch (e) {
			searchError = e instanceof Error ? e.message : 'Search failed';
		} finally {
			searching = false;
		}
	}

	async function handleSelect(result: MusicSearchResult) {
		if (selectedId === result.release_id) {
			selectedId = null;
			detail = null;
			return;
		}
		selectedId = result.release_id;
		loadingDetail = true;
		detail = null;
		try {
			detail = await fetchMusicDetail(result.release_id);
		} catch {
			// Fall back to search result data
			detail = { ...result, catalog_number: null, barcode: null, status: null, tracks: [] };
		} finally {
			loadingDetail = false;
		}
	}

	async function applyTitle(data: Partial<TitleUpdate>) {
		applying = true;
		feedback = null;
		try {
			await updateJobTitle(job.job_id, data);
			feedback = { type: 'success', message: 'Title updated' };
			onapply?.();
		} catch (e) {
			feedback = { type: 'error', message: e instanceof Error ? e.message : 'Update failed' };
		} finally {
			applying = false;
		}
	}

	function applyFromDetail() {
		if (!editTitle.trim()) return;
		applyTitle({
			title: editTitle.trim(),
			year: editYear.trim() || undefined,
			video_type: 'music',
			poster_url: editPosterUrl.trim() || undefined
		});
	}

	function backToResults() {
		detail = null;
		selectedId = null;
	}

	function handleSearchKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') handleSearch();
	}

	function handleImgError(e: Event) {
		const img = e.target as HTMLImageElement;
		img.style.display = 'none';
		const placeholder = img.nextElementSibling as HTMLElement | null;
		if (placeholder) placeholder.style.display = '';
	}

	function formatDuration(ms: number | null): string {
		if (!ms) return '--';
		const totalSec = Math.round(ms / 1000);
		const m = Math.floor(totalSec / 60);
		const s = totalSec % 60;
		return `${m}:${s.toString().padStart(2, '0')}`;
	}

	let activeFilterCount = $derived(
		[filterType, filterFormat, filterCountry.trim(), filterStatus].filter(Boolean).length
	);

	function clearFilters() {
		filterType = '';
		filterFormat = '';
		filterCountry = '';
		filterStatus = '';
	}

	const btnBase =
		'rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-50 transition-colors';
	const inputBase =
		'rounded-lg border border-primary/25 bg-primary/5 px-3 py-1.5 text-sm text-gray-900 focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white';
	const selectBase =
		'rounded-lg border border-primary/25 bg-primary/5 px-2 py-1.5 text-xs text-gray-900 focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white';
</script>

<div class="space-y-4">
	<!-- Search form -->
	<div class="flex flex-wrap items-end gap-2">
		<label class="flex-1 min-w-[200px]">
			<span class="mb-0.5 block text-[10px] font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Album / Title</span>
			<input
				type="text"
				bind:value={query}
				onkeydown={handleSearchKeydown}
				onfocus={(e) => (e.target as HTMLInputElement).select()}
				placeholder="Album or title..."
				class="w-full {inputBase}"
			/>
		</label>
		<label>
			<span class="mb-0.5 block text-[10px] font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Artist</span>
			<input
				type="text"
				bind:value={artistInput}
				onkeydown={handleSearchKeydown}
				placeholder="Artist (optional)"
				class="w-44 {inputBase}"
			/>
		</label>
		<label>
			<span class="mb-0.5 block text-[10px] font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Type</span>
			<select bind:value={filterType} class="{selectBase}">
				<option value="">Any</option>
				<option value="album">Album</option>
				<option value="single">Single</option>
				<option value="ep">EP</option>
				<option value="compilation">Compilation</option>
				<option value="live">Live</option>
				<option value="soundtrack">Soundtrack</option>
			</select>
		</label>
		<label>
			<span class="mb-0.5 block text-[10px] font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Format</span>
			<select bind:value={filterFormat} class="{selectBase}">
				<option value="">Any</option>
				<option value="CD">CD</option>
				<option value="Vinyl">Vinyl</option>
				<option value="Digital Media">Digital</option>
				<option value="Cassette">Cassette</option>
				<option value="SACD">SACD</option>
			</select>
		</label>
		<label>
			<span class="mb-0.5 block text-[10px] font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Country</span>
			<input
				type="text"
				bind:value={filterCountry}
				onkeydown={handleSearchKeydown}
				placeholder="US, GB..."
				class="w-20 {selectBase}"
			/>
		</label>
		<label>
			<span class="mb-0.5 block text-[10px] font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Status</span>
			<select bind:value={filterStatus} class="{selectBase}">
				<option value="">Any</option>
				<option value="official">Official</option>
				<option value="promotional">Promotional</option>
				<option value="bootleg">Bootleg</option>
			</select>
		</label>
		{#if activeFilterCount > 0}
			<button
				onclick={clearFilters}
				class="rounded-lg px-2 py-1.5 text-xs text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
			>
				Clear
			</button>
		{/if}
		<button
			onclick={handleSearch}
			disabled={searching || !query.trim()}
			class="{btnBase} self-end bg-primary text-on-primary hover:bg-primary-hover dark:bg-primary dark:hover:bg-primary-hover"
		>
			{searching ? 'Searching...' : 'Search'}
		</button>
	</div>

	{#if searchError}
		<p class="text-sm text-gray-500 dark:text-gray-400">{searchError}</p>
	{/if}

	<!-- Results grid (hidden when detail is shown) -->
	{#if !detail && results.length > 0}
		<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
			{#each results as result}
				<button
					onclick={() => handleSelect(result)}
					class="group flex flex-col overflow-hidden rounded-lg border text-left transition-all {selectedId === result.release_id
						? 'border-primary ring-2 ring-primary/30'
						: 'border-primary/20 hover:border-primary/40 dark:border-primary/20 dark:hover:border-primary/40'}"
				>
					<div class="relative aspect-square w-full">
						{#if result.poster_url}
							<img
								src={result.poster_url}
								alt={result.title}
								class="aspect-square w-full object-cover"
								loading="lazy"
								onerror={handleImgError}
							/>
						{/if}
						<div
							class="flex aspect-square w-full items-center justify-center bg-primary/10 text-gray-400 dark:bg-primary/15"
							style={result.poster_url ? 'display: none' : ''}
						>
							<svg class="h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="1.5"
									d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
								/>
							</svg>
						</div>
					</div>
					<div class="p-2">
						<p
							class="text-sm font-medium text-gray-900 group-hover:text-primary-text dark:text-white dark:group-hover:text-primary-text-dark line-clamp-2"
						>
							{result.title}
						</p>
						<p class="mt-0.5 text-xs text-gray-500 dark:text-gray-400 line-clamp-1">
							{result.artist}
						</p>
						<div class="mt-1 flex flex-wrap items-center gap-1">
							{#if result.year}
								<span class="text-xs text-gray-500 dark:text-gray-400">{result.year}</span>
							{/if}
							{#if result.release_type}
								<span class="rounded-sm bg-purple-100 px-1 py-0.5 text-[10px] font-medium text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
									{result.release_type}
								</span>
							{/if}
							{#if result.format}
								<span class="rounded-sm bg-green-100 px-1 py-0.5 text-[10px] font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">
									{result.format}
								</span>
							{/if}
							{#if result.country}
								<span class="rounded-sm bg-gray-100 px-1 py-0.5 text-[10px] font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-300">
									{result.country}
								</span>
							{/if}
							{#if result.track_count}
								<span class="rounded-sm bg-blue-100 px-1 py-0.5 text-[10px] font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
									{result.track_count} tracks
								</span>
							{/if}
						</div>
					</div>
				</button>
			{/each}
		</div>
	{/if}

	<!-- Detail panel with editable fields -->
	{#if loadingDetail}
		<div class="rounded-lg border border-primary/20 bg-page p-4 text-sm text-gray-500 dark:border-primary/20 dark:bg-page-dark dark:text-gray-400">
			Loading details...
		</div>
	{:else if detail}
		<div class="overflow-hidden rounded-lg border border-primary/20 dark:border-primary/20">
			<div class="space-y-3 p-4">
				{#if results.length > 0}
					<button
						onclick={backToResults}
						class="inline-flex items-center gap-1 text-sm text-primary hover:text-primary-hover dark:text-primary dark:hover:text-primary-hover"
					>
						<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
						</svg>
						Back to results
					</button>
				{/if}

				<!-- Album art + info summary -->
				<div class="flex gap-4">
					<div class="relative h-28 w-28 shrink-0 overflow-hidden rounded-md">
						{#if detail.poster_url}
							<img
								src={detail.poster_url}
								alt={detail.title}
								class="h-full w-full object-cover"
								onerror={handleImgError}
							/>
						{/if}
						<div
							class="flex h-full w-full items-center justify-center bg-primary/10 text-gray-400 dark:bg-primary/15"
							style={detail.poster_url ? 'display: none' : ''}
						>
							<svg class="h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="1.5"
									d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
								/>
							</svg>
						</div>
					</div>
					<div class="min-w-0 flex-1">
						<p class="text-lg font-semibold text-gray-900 dark:text-white">{detail.title}</p>
						<p class="text-sm text-gray-600 dark:text-gray-300">{detail.artist}</p>
						<div class="mt-1.5 flex flex-wrap items-center gap-1.5">
							{#if detail.year}
								<span class="text-xs text-gray-500 dark:text-gray-400">{detail.year}</span>
							{/if}
							{#if detail.release_type}
								<span class="rounded-sm bg-purple-100 px-1 py-0.5 text-[10px] font-medium text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">{detail.release_type}</span>
							{/if}
							{#if detail.format}
								<span class="rounded-sm bg-green-100 px-1 py-0.5 text-[10px] font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">{detail.format}</span>
							{/if}
							{#if detail.status}
								<span class="rounded-sm bg-blue-100 px-1 py-0.5 text-[10px] font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">{detail.status}</span>
							{/if}
							{#if detail.country}
								<span class="rounded-sm bg-gray-100 px-1 py-0.5 text-[10px] font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-300">{detail.country}</span>
							{/if}
						</div>
						<div class="mt-1.5 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-gray-500 dark:text-gray-400">
							{#if detail.label}
								<span>Label: {detail.label}</span>
							{/if}
							{#if detail.catalog_number}
								<span>Cat#: <span class="font-mono">{detail.catalog_number}</span></span>
							{/if}
							{#if detail.barcode}
								<span>Barcode: <span class="font-mono">{detail.barcode}</span></span>
							{/if}
							{#if detail.track_count}
								<span>{detail.track_count} tracks</span>
							{/if}
						</div>
					</div>
				</div>

				<!-- Track listing -->
				{#if detail.tracks && detail.tracks.length > 0}
					<div>
						<h4 class="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-300">Track Listing</h4>
						<div class="overflow-x-auto rounded-md border border-primary/15 dark:border-primary/20">
							<table class="w-full text-left text-xs">
								<thead class="bg-page text-gray-500 dark:bg-primary/5 dark:text-gray-400">
									<tr>
										<th class="w-10 px-3 py-1.5 font-medium">#</th>
										<th class="px-3 py-1.5 font-medium">Title</th>
										<th class="w-16 px-3 py-1.5 font-medium text-right">Duration</th>
									</tr>
								</thead>
								<tbody class="divide-y divide-gray-100 dark:divide-gray-700/50">
									{#each detail.tracks as track}
										<tr>
											<td class="px-3 py-1.5 font-mono text-gray-500 dark:text-gray-400">{track.number}</td>
											<td class="px-3 py-1.5 text-gray-700 dark:text-gray-300">{track.title}</td>
											<td class="px-3 py-1.5 text-right font-mono text-gray-500 dark:text-gray-400">{formatDuration(track.length_ms)}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				{/if}

				<!-- Editable fields -->
				<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
					<label class="sm:col-span-2">
						<span class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Title</span>
						<input type="text" bind:value={editTitle} class="w-full {inputBase}" />
					</label>
					<label>
						<span class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Year</span>
						<input type="text" bind:value={editYear} class="w-full {inputBase}" />
					</label>
					<label>
						<span class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Poster URL</span>
						<input type="text" bind:value={editPosterUrl} placeholder="https://..." class="w-full {inputBase}" />
					</label>
				</div>
				<div class="flex items-center gap-2">
					<button
						onclick={applyFromDetail}
						disabled={applying || !editTitle.trim()}
						class="{btnBase} bg-green-600 text-white hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600"
					>
						{applying ? 'Applying...' : 'Apply This Title'}
					</button>
					{#if feedback}
						<span
							class="text-xs {feedback.type === 'success'
								? 'text-green-600 dark:text-green-400'
								: 'text-red-600 dark:text-red-400'}"
						>
							{feedback.message}
						</span>
					{/if}
				</div>
			</div>
		</div>
	{/if}
</div>
