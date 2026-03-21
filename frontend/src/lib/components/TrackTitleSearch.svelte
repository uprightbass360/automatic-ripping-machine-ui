<script lang="ts">
	import type { Track, TrackTitleUpdate, SearchResult, MediaDetail } from '$lib/types/arm';
	import { searchMetadata, fetchMediaDetail, updateTrackTitle, clearTrackTitle } from '$lib/api/jobs';
	import { posterSrc } from '$lib/utils/poster';

	interface Props {
		jobId: number;
		track: Track;
		onapply?: () => void;
		onclose?: () => void;
	}

	let { jobId, track, onapply, onclose }: Props = $props();

	let query = $state(track.title || track.basename || '');
	let yearInput = $state(track.year || '');
	let imdbInput = $state('');
	let searching = $state(false);
	let results = $state<SearchResult[]>([]);
	let searchError = $state<string | null>(null);

	let detail = $state<MediaDetail | null>(null);
	let loadingDetail = $state(false);

	let applying = $state(false);
	let clearing = $state(false);
	let feedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);

	// Editable fields populated from detail
	let editTitle = $state('');
	let editYear = $state('');
	let editType = $state<'movie' | 'series'>('movie');
	let editImdbId = $state('');
	let editPosterUrl = $state('');

	$effect(() => {
		if (detail) {
			editTitle = detail.title;
			editYear = detail.year;
			editType = detail.media_type === 'series' ? 'series' : 'movie';
			editImdbId = detail.imdb_id ?? '';
			editPosterUrl = detail.poster_url ?? '';
		}
	});

	async function handleSearch() {
		const imdb = imdbInput.trim();
		if (imdb) {
			searching = true;
			searchError = null;
			results = [];
			detail = null;
			try {
				detail = await fetchMediaDetail(imdb);
			} catch (e) {
				searchError = e instanceof Error ? e.message : 'IMDb lookup failed';
			} finally {
				searching = false;
			}
			return;
		}
		if (!query.trim()) return;
		searching = true;
		searchError = null;
		results = [];
		detail = null;
		try {
			results = await searchMetadata(query.trim(), yearInput.trim() || undefined);
			if (results.length === 0) searchError = 'No results found.';
		} catch (e) {
			searchError = e instanceof Error ? e.message : 'Search failed';
		} finally {
			searching = false;
		}
	}

	async function handleSelect(result: SearchResult) {
		if (!result.imdb_id) {
			detail = { ...result, plot: null, background_url: null };
			return;
		}
		loadingDetail = true;
		detail = null;
		try {
			detail = await fetchMediaDetail(result.imdb_id);
		} catch {
			detail = { ...result, plot: null, background_url: null };
		} finally {
			loadingDetail = false;
		}
	}

	async function applyFromDetail() {
		if (!editTitle.trim()) return;
		applying = true;
		feedback = null;
		try {
			const data: Partial<TrackTitleUpdate> = {
				title: editTitle.trim(),
				year: editYear.trim() || undefined,
				video_type: editType,
				imdb_id: editImdbId.trim() || undefined,
				poster_url: editPosterUrl.trim() || undefined,
			};
			await updateTrackTitle(jobId, track.track_id, data);
			feedback = { type: 'success', message: 'Track title updated' };
			onapply?.();
		} catch (e) {
			feedback = { type: 'error', message: e instanceof Error ? e.message : 'Update failed' };
		} finally {
			applying = false;
		}
	}

	async function handleClear() {
		clearing = true;
		feedback = null;
		try {
			await clearTrackTitle(jobId, track.track_id);
			feedback = { type: 'success', message: 'Reverted to job title' };
			onapply?.();
		} catch (e) {
			feedback = { type: 'error', message: e instanceof Error ? e.message : 'Clear failed' };
		} finally {
			clearing = false;
		}
	}

	function handleSearchKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') handleSearch();
	}

	const btnBase = 'rounded-md px-2 py-1 text-xs font-medium disabled:opacity-50 transition-colors';
	const inputBase = 'rounded-md border border-primary/25 bg-primary/5 px-2 py-1 text-sm text-gray-900 focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white';
</script>

<div class="space-y-3 rounded-md border border-primary/15 bg-primary/5 p-3 dark:border-primary/20 dark:bg-primary/10">
	<div class="flex items-center justify-between">
		<h5 class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
			Track {track.track_number} Title Override
		</h5>
		<div class="flex items-center gap-1.5">
			{#if track.title}
				<button onclick={handleClear} disabled={clearing} class="{btnBase} text-amber-600 ring-1 ring-amber-300 hover:bg-amber-50 dark:text-amber-400 dark:ring-amber-700 dark:hover:bg-amber-900/20">
					{clearing ? 'Clearing...' : 'Clear Override'}
				</button>
			{/if}
			{#if onclose}
				<button onclick={onclose} title="Close" class="{btnBase} text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
					<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
				</button>
			{/if}
		</div>
	</div>

	<!-- Search form -->
	<div class="flex flex-wrap gap-1.5">
		<input type="text" bind:value={query} onkeydown={handleSearchKeydown} placeholder="Title..." class="min-w-[150px] flex-1 {inputBase}" />
		<input type="text" bind:value={yearInput} onkeydown={handleSearchKeydown} placeholder="Year" class="w-16 {inputBase}" />
		<input type="text" bind:value={imdbInput} onkeydown={handleSearchKeydown} placeholder="tt..." class="w-28 {inputBase}" />
		<button onclick={handleSearch} disabled={searching || (!query.trim() && !imdbInput.trim())} class="{btnBase} bg-primary text-on-primary hover:bg-primary-hover">
			{searching ? '...' : 'Search'}
		</button>
	</div>

	{#if searchError}
		{#if searchError.toLowerCase().includes('api key')}
			<div class="rounded-md border border-amber-300 bg-amber-50 px-2 py-1.5 text-xs text-amber-800 dark:border-amber-600/40 dark:bg-amber-900/20 dark:text-amber-300">
				<p>{searchError}</p>
				<p class="mt-0.5 text-amber-600 dark:text-amber-400">Configure API keys in <a href="/settings" class="underline hover:no-underline">Settings</a>.</p>
			</div>
		{:else}
			<p class="text-xs text-gray-500 dark:text-gray-400">{searchError}</p>
		{/if}
	{/if}

	<!-- Results -->
	{#if !detail && results.length > 0}
		<div class="flex flex-wrap gap-2">
			{#each results as result}
				<button onclick={() => handleSelect(result)} class="flex items-center gap-2 rounded-md border border-primary/15 px-2 py-1 text-left text-xs hover:border-primary/40 dark:border-primary/20">
					{#if result.poster_url}
						<img src={posterSrc(result.poster_url)} alt="" class="h-10 w-7 rounded-sm object-cover" loading="lazy" />
					{/if}
					<div>
						<p class="font-medium text-gray-900 dark:text-white">{result.title}</p>
						<p class="text-gray-500 dark:text-gray-400">{result.year} &middot; {result.media_type}</p>
					</div>
				</button>
			{/each}
		</div>
	{/if}

	<!-- Detail / Edit -->
	{#if loadingDetail}
		<p class="text-xs text-gray-400">Loading...</p>
	{:else if detail}
		<div class="space-y-2">
			<div class="grid grid-cols-2 gap-2">
				<label class="col-span-2">
					<span class="mb-0.5 block text-[10px] font-medium text-gray-500 dark:text-gray-400">Title</span>
					<input type="text" bind:value={editTitle} class="w-full {inputBase}" />
				</label>
				<label>
					<span class="mb-0.5 block text-[10px] font-medium text-gray-500 dark:text-gray-400">Year</span>
					<input type="text" bind:value={editYear} class="w-full {inputBase}" />
				</label>
				<label>
					<span class="mb-0.5 block text-[10px] font-medium text-gray-500 dark:text-gray-400">Type</span>
					<select bind:value={editType} class="w-full {inputBase}">
						<option value="movie">Movie</option>
						<option value="series">Series</option>
					</select>
				</label>
				<label>
					<span class="mb-0.5 block text-[10px] font-medium text-gray-500 dark:text-gray-400">IMDb ID</span>
					<input type="text" bind:value={editImdbId} placeholder="tt..." class="w-full {inputBase}" />
				</label>
				<label>
					<span class="mb-0.5 block text-[10px] font-medium text-gray-500 dark:text-gray-400">Poster URL</span>
					<input type="text" bind:value={editPosterUrl} placeholder="https://..." class="w-full {inputBase}" />
				</label>
			</div>
			<div class="flex items-center gap-2">
				<button onclick={applyFromDetail} disabled={applying || !editTitle.trim()} class="{btnBase} bg-green-600 text-white hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600">
					{applying ? 'Applying...' : 'Apply'}
				</button>
				{#if results.length > 0}
					<button onclick={() => { detail = null; }} class="{btnBase} text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
						Back
					</button>
				{/if}
				{#if feedback}
					<span class="text-xs {feedback.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">{feedback.message}</span>
				{/if}
			</div>
		</div>
	{/if}
</div>
