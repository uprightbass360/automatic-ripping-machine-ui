<script lang="ts">
	import type { JobDetail } from '$lib/types/arm';
	import { tvdbMatch, fetchTvdbEpisodes, type TvdbMatch, type TvdbMatchResponse, type TvdbAlternative } from '$lib/api/jobs';

	interface Props {
		job: JobDetail;
		onapply?: () => void;
	}

	let { job, onapply }: Props = $props();

	let seasonInput = $state(job.season || job.season_auto || '');
	let toleranceInput = $state('300');
	let autoDetect = $state(!seasonInput);
	let loading = $state(false);
	let error = $state<string | null>(null);
	let result = $state<TvdbMatchResponse | null>(null);
	let applying = $state(false);
	let applyFeedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);

	// Build a map of track lengths for display
	let trackLengthMap = $derived(
		Object.fromEntries((job.tracks || []).map((t) => [t.track_number, t.length]))
	);

	async function handlePreview() {
		loading = true;
		error = null;
		result = null;
		applyFeedback = null;
		try {
			result = await tvdbMatch(job.job_id, {
				season: autoDetect ? null : Number(seasonInput) || null,
				tolerance: Number(toleranceInput) || 300,
				apply: false
			});
		} catch (e) {
			error = e instanceof Error ? e.message : 'TVDB match failed';
		} finally {
			loading = false;
		}
	}

	async function handleApply() {
		if (!result || !result.matches.length) return;
		applying = true;
		applyFeedback = null;
		try {
			await tvdbMatch(job.job_id, {
				season: result.season ?? null,
				tolerance: Number(toleranceInput) || 300,
				apply: true
			});
			applyFeedback = { type: 'success', message: `Applied ${result.matches.length} episode matches (S${String(result.season).padStart(2, '0')})` };
			onapply?.();
		} catch (e) {
			applyFeedback = { type: 'error', message: e instanceof Error ? e.message : 'Apply failed' };
		} finally {
			applying = false;
		}
	}

	function formatRuntime(seconds: number | null): string {
		if (!seconds) return '--';
		const m = Math.floor(seconds / 60);
		const s = seconds % 60;
		return `${m}:${String(s).padStart(2, '0')}`;
	}

	function formatDelta(trackLen: number | null, epRuntime: number): string {
		if (!trackLen) return '--';
		const delta = trackLen - epRuntime;
		const sign = delta >= 0 ? '+' : '';
		return `${sign}${delta}s`;
	}

	const btnBase =
		'rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-50 transition-colors';
	const inputBase =
		'rounded-lg border border-primary/25 bg-primary/5 px-3 py-1.5 text-sm text-gray-900 focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white';
</script>

<div class="space-y-4">
	<!-- Current status -->
	<div class="flex items-center gap-2 text-sm">
		{#if job.tvdb_id}
			<span class="text-gray-500 dark:text-gray-400">TVDB ID: {job.tvdb_id}</span>
		{:else}
			<span class="text-gray-400 dark:text-gray-500">No TVDB ID yet (will resolve on first match)</span>
		{/if}
		{#if job.season_auto}
			<span class="rounded-sm bg-blue-100 px-1.5 py-0.5 text-[10px] font-semibold text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
				Season {job.season_auto}
			</span>
		{/if}
	</div>

	<!-- Controls -->
	<div class="flex flex-wrap items-end gap-3">
		<label class="flex items-center gap-2">
			<input
				type="checkbox"
				bind:checked={autoDetect}
				class="h-4 w-4 rounded-sm border-primary/25 text-primary focus:ring-primary dark:border-primary/30 dark:bg-primary/10"
			/>
			<span class="text-sm text-gray-700 dark:text-gray-300">Auto-detect season</span>
		</label>
		{#if !autoDetect}
			<label>
				<span class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Season</span>
				<input type="number" bind:value={seasonInput} min="1" class="w-20 {inputBase}" />
			</label>
		{/if}
		<label>
			<span class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Tolerance (sec)</span>
			<input type="number" bind:value={toleranceInput} min="60" step="30" class="w-24 {inputBase}" />
		</label>
		<button
			onclick={handlePreview}
			disabled={loading}
			class="{btnBase} bg-primary text-on-primary hover:bg-primary-hover dark:bg-primary dark:hover:bg-primary-hover"
		>
			{loading ? 'Matching...' : 'Preview Match'}
		</button>
	</div>

	{#if error}
		<p class="text-sm text-red-600 dark:text-red-400">{error}</p>
	{/if}

	<!-- Results -->
	{#if result}
		<div class="space-y-3">
			<!-- Summary -->
			<div class="flex flex-wrap items-center gap-3 text-sm">
				<span class="font-medium text-gray-900 dark:text-white">
					Season {result.season}: {result.match_count} match{result.match_count !== 1 ? 'es' : ''}
				</span>
				{#if result.score > 0}
					<span class="text-gray-500 dark:text-gray-400">avg delta {result.score}s</span>
				{/if}
				{#if result.alternatives.length > 0}
					<span class="text-xs text-gray-400 dark:text-gray-500">
						Alternatives: {result.alternatives.map((a) => `S${String(a.season).padStart(2, '0')}(${a.match_count})`).join(', ')}
					</span>
				{/if}
			</div>

			<!-- Match table -->
			{#if result.matches.length > 0}
				<div class="overflow-x-auto rounded-lg border border-primary/20 dark:border-primary/20">
					<table class="w-full text-left text-sm">
						<thead class="bg-page text-gray-600 dark:bg-primary/5 dark:text-gray-400">
							<tr>
								<th class="px-4 py-2 font-medium">Track</th>
								<th class="px-4 py-2 font-medium">Track Length</th>
								<th class="px-4 py-2 font-medium">Episode</th>
								<th class="px-4 py-2 font-medium">Episode Name</th>
								<th class="px-4 py-2 font-medium">TVDB Runtime</th>
								<th class="px-4 py-2 font-medium">Delta</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
							{#each result.matches as match}
								{@const trackLen = trackLengthMap[match.track_number] ?? null}
								{@const delta = trackLen != null ? Math.abs(trackLen - match.episode_runtime) : null}
								<tr class="hover:bg-page dark:hover:bg-gray-800/50">
									<td class="px-4 py-2 font-mono">{match.track_number}</td>
									<td class="px-4 py-2">{formatRuntime(trackLen)}</td>
									<td class="px-4 py-2 font-medium">S{String(result.season).padStart(2, '0')}E{String(match.episode_number).padStart(2, '0')}</td>
									<td class="px-4 py-2 text-gray-900 dark:text-white">{match.episode_name}</td>
									<td class="px-4 py-2">{formatRuntime(match.episode_runtime)}</td>
									<td class="px-4 py-2 font-mono text-xs {delta != null && delta < 60 ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}">
										{formatDelta(trackLen, match.episode_runtime)}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>

				<!-- Unmatched tracks -->
				{@const matchedTracks = new Set(result.matches.map((m) => m.track_number))}
				{@const unmatchedTracks = (job.tracks || []).filter(
					(t) => t.track_number && !matchedTracks.has(t.track_number) && (t.length ?? 0) >= 120
				)}
				{#if unmatchedTracks.length > 0}
					<p class="text-xs text-gray-400 dark:text-gray-500">
						Unmatched tracks: {unmatchedTracks.map((t) => `#${t.track_number} (${formatRuntime(t.length)})`).join(', ')}
					</p>
				{/if}

				<!-- Apply button -->
				<div class="flex items-center gap-3">
					<button
						onclick={handleApply}
						disabled={applying}
						class="{btnBase} bg-green-600 text-white hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600"
					>
						{applying ? 'Applying...' : `Apply ${result.matches.length} Matches`}
					</button>
					{#if applyFeedback}
						<span class="text-xs {applyFeedback.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
							{applyFeedback.message}
						</span>
					{/if}
				</div>
			{:else}
				<p class="text-sm text-gray-400 dark:text-gray-500">No matches found. Try adjusting the tolerance or season.</p>
			{/if}
		</div>
	{/if}
</div>
