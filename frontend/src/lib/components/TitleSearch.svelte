<script lang="ts">
	import type { Job, SearchResult, MediaDetail, TitleUpdate } from '$lib/types/arm';
	import { searchMetadata, fetchMediaDetail, updateJobTitle } from '$lib/api/jobs';

	interface Props {
		job: Job;
		onapply?: () => void;
	}

	let { job, onapply }: Props = $props();

	let mode = $state<'search' | 'custom'>('search');
	let query = $state(job.title || job.label || '');
	let yearInput = $state(job.year || '');
	let searching = $state(false);
	let results = $state<SearchResult[]>([]);
	let searchError = $state<string | null>(null);

	let selectedImdb = $state<string | null>(null);
	let detail = $state<MediaDetail | null>(null);
	let loadingDetail = $state(false);

	let applying = $state(false);
	let feedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);

	// Custom title fields
	let customTitle = $state(job.title || '');
	let customYear = $state(job.year || '');
	let customType = $state(job.video_type || 'movie');

	async function handleSearch() {
		if (!query.trim()) return;
		searching = true;
		searchError = null;
		results = [];
		selectedImdb = null;
		detail = null;
		try {
			results = await searchMetadata(query.trim(), yearInput.trim() || undefined);
			if (results.length === 0) {
				searchError = 'No results found. Try a different search term.';
			}
		} catch (e) {
			searchError = e instanceof Error ? e.message : 'Search failed';
		} finally {
			searching = false;
		}
	}

	async function handleSelect(result: SearchResult) {
		if (!result.imdb_id) {
			// No IMDb ID — apply directly from search result
			detail = { ...result, plot: null, background_url: null };
			selectedImdb = null;
			return;
		}
		if (selectedImdb === result.imdb_id) {
			selectedImdb = null;
			detail = null;
			return;
		}
		selectedImdb = result.imdb_id;
		loadingDetail = true;
		detail = null;
		try {
			detail = await fetchMediaDetail(result.imdb_id);
		} catch {
			// Fall back to search result data
			detail = { ...result, plot: null, background_url: null };
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
		if (!detail) return;
		applyTitle({
			title: detail.title,
			year: detail.year,
			video_type: detail.media_type === 'series' ? 'series' : 'movie',
			imdb_id: detail.imdb_id ?? undefined,
			poster_url: detail.poster_url ?? undefined
		});
	}

	function applyCustom() {
		if (!customTitle.trim()) return;
		applyTitle({
			title: customTitle.trim(),
			year: customYear.trim() || undefined,
			video_type: customType
		});
	}

	function handleSearchKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') handleSearch();
	}

	function handleCustomKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') applyCustom();
	}

	const btnBase =
		'rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-50 transition-colors';
</script>

<div class="space-y-4">
	<!-- Mode tabs -->
	<div class="flex gap-2 border-b border-gray-200 dark:border-gray-700 pb-2">
		<button
			onclick={() => (mode = 'search')}
			class="rounded-t px-3 py-1.5 text-sm font-medium transition-colors {mode === 'search'
				? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
				: 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}"
		>
			Search Title
		</button>
		<button
			onclick={() => (mode = 'custom')}
			class="rounded-t px-3 py-1.5 text-sm font-medium transition-colors {mode === 'custom'
				? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
				: 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'}"
		>
			Custom Title
		</button>
	</div>

	{#if mode === 'search'}
		<!-- Search form -->
		<div class="flex flex-wrap gap-2">
			<input
				type="text"
				bind:value={query}
				onkeydown={handleSearchKeydown}
				placeholder="Title..."
				class="flex-1 min-w-[200px] rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
			/>
			<input
				type="text"
				bind:value={yearInput}
				onkeydown={handleSearchKeydown}
				placeholder="Year"
				class="w-20 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
			/>
			<button
				onclick={handleSearch}
				disabled={searching || !query.trim()}
				class="{btnBase} bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
			>
				{searching ? 'Searching...' : 'Search'}
			</button>
		</div>

		{#if searchError}
			<p class="text-sm text-gray-500 dark:text-gray-400">{searchError}</p>
		{/if}

		<!-- Results grid -->
		{#if results.length > 0}
			<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
				{#each results as result}
					<button
						onclick={() => handleSelect(result)}
						class="group flex flex-col overflow-hidden rounded-lg border text-left transition-all {selectedImdb === result.imdb_id
							? 'border-blue-500 ring-2 ring-blue-500/30'
							: 'border-gray-200 hover:border-gray-400 dark:border-gray-700 dark:hover:border-gray-500'}"
					>
						{#if result.poster_url}
							<img
								src={result.poster_url}
								alt={result.title}
								class="aspect-[2/3] w-full object-cover"
								loading="lazy"
							/>
						{:else}
							<div
								class="flex aspect-[2/3] w-full items-center justify-center bg-gray-100 text-gray-400 dark:bg-gray-800"
							>
								<svg class="h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="1.5"
										d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z"
									/>
								</svg>
							</div>
						{/if}
						<div class="p-2">
							<p
								class="text-sm font-medium text-gray-900 group-hover:text-blue-600 dark:text-white dark:group-hover:text-blue-400 line-clamp-2"
							>
								{result.title}
							</p>
							<div class="mt-1 flex items-center gap-1.5">
								<span class="text-xs text-gray-500 dark:text-gray-400">{result.year}</span>
								<span
									class="rounded px-1 py-0.5 text-[10px] font-medium uppercase {result.media_type === 'series'
										? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
										: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'}"
								>
									{result.media_type}
								</span>
							</div>
						</div>
					</button>
				{/each}
			</div>
		{/if}

		<!-- Detail panel -->
		{#if loadingDetail}
			<div class="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-500 dark:border-gray-700 dark:bg-gray-800/50 dark:text-gray-400">
				Loading details...
			</div>
		{:else if detail}
			<div class="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700">
				{#if detail.background_url}
					<div
						class="relative h-40 bg-cover bg-center"
						style="background-image: url({detail.background_url})"
					>
						<div class="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent"></div>
						<div class="absolute bottom-3 left-4 right-4">
							<h3 class="text-lg font-bold text-white">{detail.title}</h3>
							<p class="text-sm text-gray-300">
								{detail.year}
								{#if detail.media_type}
									&middot;
									<span class="capitalize">{detail.media_type}</span>
								{/if}
								{#if detail.imdb_id}
									&middot; {detail.imdb_id}
								{/if}
							</p>
						</div>
					</div>
				{:else}
					<div class="border-b border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-700 dark:bg-gray-800/50">
						<h3 class="font-bold text-gray-900 dark:text-white">{detail.title}</h3>
						<p class="text-sm text-gray-500 dark:text-gray-400">
							{detail.year}
							{#if detail.media_type}
								&middot;
								<span class="capitalize">{detail.media_type}</span>
							{/if}
							{#if detail.imdb_id}
								&middot; {detail.imdb_id}
							{/if}
						</p>
					</div>
				{/if}
				<div class="space-y-3 p-4">
					{#if detail.plot}
						<p class="text-sm text-gray-700 dark:text-gray-300">{detail.plot}</p>
					{/if}
					<div class="flex items-center gap-2">
						<button
							onclick={applyFromDetail}
							disabled={applying}
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
	{:else}
		<!-- Custom title form -->
		<div class="space-y-3">
			<div class="flex flex-wrap gap-2">
				<input
					type="text"
					bind:value={customTitle}
					onkeydown={handleCustomKeydown}
					placeholder="Title"
					class="flex-1 min-w-[200px] rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
				/>
				<input
					type="text"
					bind:value={customYear}
					onkeydown={handleCustomKeydown}
					placeholder="Year"
					class="w-20 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
				/>
				<select
					bind:value={customType}
					class="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
				>
					<option value="movie">Movie</option>
					<option value="series">Series</option>
				</select>
			</div>
			<div class="flex items-center gap-2">
				<button
					onclick={applyCustom}
					disabled={applying || !customTitle.trim()}
					class="{btnBase} bg-green-600 text-white hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600"
				>
					{applying ? 'Saving...' : 'Save Title'}
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
	{/if}
</div>
