<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { fetchJob, retranscodeJob, fetchMusicDetail, toggleMultiTitle } from '$lib/api/jobs';
	import type { JobDetail, MusicDetail } from '$lib/types/arm';
	import JobActions from '$lib/components/JobActions.svelte';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import TitleSearch from '$lib/components/TitleSearch.svelte';
	import MusicSearch from '$lib/components/MusicSearch.svelte';
	import RipSettings from '$lib/components/RipSettings.svelte';
	import TranscodeOverrides from '$lib/components/TranscodeOverrides.svelte';
	import CrcLookup from '$lib/components/CrcLookup.svelte';
	import InlineLogFeed from '$lib/components/InlineLogFeed.svelte';
	import TrackTitleSearch from '$lib/components/TrackTitleSearch.svelte';
	import { formatDateTime, timeAgo } from '$lib/utils/format';
	import { discTypeLabel, isJobActive } from '$lib/utils/job-type';

	let job = $state<JobDetail | null>(null);
	let error = $state<string | null>(null);
	let showTitleSearch = $state(false);
	let showMusicSearch = $state(false);
	let showCrcLookup = $state(false);
	let showRipSettings = $state(false);
	let showTranscodeOverrides = $state(false);
	let retranscoding = $state(false);
	let retranscodeFeedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);

	// MusicBrainz track listing (fetched when DB tracks are empty for music discs)
	let musicDetail = $state<MusicDetail | null>(null);
	let musicDetailLoading = $state(false);
	let togglingMultiTitle = $state(false);
	let editingTrackId = $state<number | null>(null);

	async function handleRetranscode() {
		if (!job) return;
		retranscoding = true;
		retranscodeFeedback = null;
		try {
			const result = await retranscodeJob(job.job_id);
			retranscodeFeedback = { type: 'success', message: result.message || 'Queued for transcoding' };
		} catch (e) {
			retranscodeFeedback = { type: 'error', message: e instanceof Error ? e.message : 'Failed to queue' };
		} finally {
			retranscoding = false;
		}
	}

	async function handleToggleMultiTitle() {
		if (!job) return;
		togglingMultiTitle = true;
		try {
			await toggleMultiTitle(job.job_id, !job.multi_title);
			await loadJob();
		} catch {
			// next refresh will reconcile
		} finally {
			togglingMultiTitle = false;
		}
	}

	function handleTrackTitleApply() {
		editingTrackId = null;
		loadJob();
	}

	let isVideoDisc = $derived(
		job?.disctype === 'dvd' || job?.disctype === 'bluray' || job?.disctype === 'bluray4k'
	);

	let isMusicDisc = $derived(
		job?.disctype === 'music' || job?.video_type === 'music'
	);

	let hasCrcData = $derived(
		job?.disctype === 'dvd' || !!job?.crc_id
	);

	let hasAutoManualDiff = $derived(
		job != null &&
			job.title_auto != null &&
			job.title != null &&
			job.title_auto !== job.title
	);

	function extractReleaseId(posterUrl: string | null): string | null {
		if (!posterUrl) return null;
		const match = posterUrl.match(/coverartarchive\.org\/release\/([a-f0-9-]+)\//);
		return match?.[1] ?? null;
	}

	async function loadMusicTracks() {
		if (!job || !isMusicDisc || job.tracks.length > 0) return;
		const releaseId = extractReleaseId(job.poster_url);
		if (!releaseId) return;
		musicDetailLoading = true;
		try {
			musicDetail = await fetchMusicDetail(releaseId);
		} catch {
			musicDetail = null;
		} finally {
			musicDetailLoading = false;
		}
	}

	async function loadJob() {
		const id = Number($page.params.id);
		try {
			job = await fetchJob(id);
		} catch (e) {
			if (e instanceof Error && e.message.includes('404')) {
				goto('/jobs');
				return;
			}
			error = e instanceof Error ? e.message : 'Failed to load job';
		}
	}

	function formatDurationMs(ms: number | null): string {
		if (!ms) return '--';
		const totalSec = Math.round(ms / 1000);
		const m = Math.floor(totalSec / 60);
		const s = totalSec % 60;
		return `${m}:${s.toString().padStart(2, '0')}`;
	}

	function handleTitleApply() {
		showTitleSearch = false;
		loadJob();
	}

	function handleConfigSaved() {
		showRipSettings = false;
		loadJob();
	}

	onMount(() => {
		let stopped = false;
		async function poll() {
			while (!stopped) {
				await new Promise((r) => setTimeout(r, 5000));
				if (job && isJobActive(job.status)) {
					await loadJob();
				} else {
					break;
				}
			}
		}
		loadJob().then(() => { loadMusicTracks(); return poll(); });
		return () => {
			stopped = true;
		};
	});
</script>

<svelte:head>
	<title>ARM - {job?.title || 'Job Detail'}</title>
</svelte:head>

{#if error}
	<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
		{error}
	</div>
{:else if !job}
	<div class="py-8 text-center text-gray-400">Loading...</div>
{:else}
	<div class="space-y-6">
		<!-- Back link -->
		<a href="/" class="inline-flex items-center gap-1 text-sm text-primary-text hover:underline dark:text-primary-text-dark">
			<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
			</svg>
			Back to Dashboard
		</a>

		<!-- Header -->
		<div class="flex flex-col gap-6 md:flex-row">
			{#if job.poster_url}
				<img
					src={job.poster_url}
					alt={job.title ?? 'Poster'}
					class="rounded-lg object-cover shadow-md {isMusicDisc ? 'h-48 w-48' : 'h-64 w-44'}"
				/>
			{/if}
			<div class="flex-1 space-y-3">
				<div class="flex flex-wrap items-center gap-3">
					<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
						{job.title || job.label || 'Untitled'}
					</h1>
					{#if job.year}
						<span class="text-lg text-gray-500 dark:text-gray-400">({job.year})</span>
					{/if}
					<StatusBadge status={job.status} />
					{#if job.multi_title}
						<span class="rounded-sm bg-purple-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">Multi-Title</span>
					{/if}
				</div>

				<JobActions {job} onaction={loadJob} />

				{#if isVideoDisc && (job.status === 'success' || job.status === 'fail')}
					<div class="flex items-center gap-3">
						<button
							onclick={handleRetranscode}
							disabled={retranscoding}
							class="rounded-lg px-3 py-1.5 text-sm font-medium bg-indigo-100 text-indigo-700 hover:bg-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 dark:hover:bg-indigo-900/50 disabled:opacity-50 transition-colors"
						>
							{retranscoding ? 'Queuing...' : 'Re-transcode'}
						</button>
						{#if retranscodeFeedback}
							<span class="text-sm {retranscodeFeedback.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
								{retranscodeFeedback.message}
							</span>
						{/if}
					</div>
				{/if}

				{#if job.imdb_id && !isMusicDisc}
					<a
						href="https://www.imdb.com/title/{job.imdb_id}"
						target="_blank"
						rel="noopener noreferrer"
						class="inline-flex items-center gap-1 rounded-sm bg-yellow-400 px-2 py-0.5 text-xs font-bold text-black"
					>
						IMDb
					</a>
				{/if}

				<dl class="grid grid-cols-2 gap-x-6 gap-y-2 text-sm md:grid-cols-3">
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Status</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{job.status ?? 'N/A'}</dd>
					</div>
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Stage</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{job.stage ?? 'N/A'}</dd>
					</div>
					{#if !isMusicDisc}
						<div>
							<dt class="text-gray-500 dark:text-gray-400">Video Type</dt>
							<dd class="font-medium text-gray-900 dark:text-white">{job.video_type ?? 'N/A'}</dd>
						</div>
					{/if}
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Disc Type</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{discTypeLabel(job.disctype)}</dd>
					</div>
					{#if isVideoDisc}
						<div>
							<dt class="text-gray-500 dark:text-gray-400">Title Mode</dt>
							<dd>
								<select
									value={job.multi_title ? 'multi' : 'single'}
									onchange={(e) => { const v = e.currentTarget.value; if ((v === 'multi') !== !!job?.multi_title) handleToggleMultiTitle(); }}
									disabled={togglingMultiTitle}
									class="rounded-sm border border-primary/25 bg-primary/5 px-1 py-0.5 text-sm font-medium text-gray-900 focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white"
								>
									<option value="single">Single Title</option>
									<option value="multi">Multi-Title</option>
								</select>
							</dd>
						</div>
					{/if}
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Device</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{job.devpath ?? 'N/A'}</dd>
					</div>
					<div>
						<dt class="text-gray-500 dark:text-gray-400">{isMusicDisc ? 'Tracks' : 'Titles'}</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{job.no_of_titles ?? 'N/A'}</dd>
					</div>
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Started</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{formatDateTime(job.start_time)}</dd>
					</div>
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Finished</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{formatDateTime(job.stop_time)}</dd>
					</div>
					<div>
						<dt class="text-gray-500 dark:text-gray-400">Duration</dt>
						<dd class="font-medium text-gray-900 dark:text-white">{job.job_length ?? 'N/A'}</dd>
					</div>
				</dl>

				{#if job.errors}
					<div class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
						<strong>Errors:</strong> {job.errors}
					</div>
				{/if}

				{#if job.logfile}
					<InlineLogFeed logfile={job.logfile} maxEntries={15} />
				{/if}
			</div>
		</div>

		<!-- Auto vs Manual title info -->
		{#if hasAutoManualDiff}
			<div class="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm dark:border-amber-800 dark:bg-amber-900/20">
				<svg class="h-4 w-4 shrink-0 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
				<span class="text-amber-800 dark:text-amber-300">
					Auto-detected: <span class="font-medium">{job.title_auto}{#if job.year_auto} ({job.year_auto}){/if}</span>
				</span>
			</div>
		{/if}

		<!-- Title search / edit -->
		{#if isVideoDisc}
			{#if !showTitleSearch}
				<button
					onclick={() => (showTitleSearch = true)}
					class="rounded-lg px-3 py-1.5 text-sm font-medium bg-indigo-100 text-indigo-700 hover:bg-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 dark:hover:bg-indigo-900/50 transition-colors"
				>
					Search / Edit Title
				</button>
			{:else}
				<section class="rounded-lg border border-primary/20 p-4 dark:border-primary/20">
					<div class="mb-3 flex items-center justify-between">
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Search / Edit Title</h2>
						<button
							onclick={() => (showTitleSearch = false)}
							aria-label="Close title search"
							class="rounded-sm p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
						>
							<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>
					<TitleSearch {job} onapply={handleTitleApply} />
				</section>
			{/if}
		{/if}

		<!-- Music search -->
		{#if isMusicDisc}
			{#if !showMusicSearch}
				<button
					onclick={() => (showMusicSearch = true)}
					class="rounded-lg px-3 py-1.5 text-sm font-medium bg-indigo-100 text-indigo-700 hover:bg-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 dark:hover:bg-indigo-900/50 transition-colors"
				>
					Search Music
				</button>
			{:else}
				<section class="rounded-lg border border-primary/20 p-4 dark:border-primary/20">
					<div class="mb-3 flex items-center justify-between">
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Search Music</h2>
						<button
							onclick={() => (showMusicSearch = false)}
							aria-label="Close music search"
							class="rounded-sm p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
						>
							<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>
					<MusicSearch {job} onapply={handleTitleApply} />
				</section>
			{/if}
		{/if}

		<!-- CRC Database -->
		{#if hasCrcData}
			{#if !showCrcLookup}
				<button
					onclick={() => (showCrcLookup = true)}
					class="rounded-lg px-3 py-1.5 text-sm font-medium bg-primary/5 text-gray-700 ring-1 ring-primary/25 hover:bg-primary/10 dark:bg-primary/10 dark:text-gray-200 dark:ring-primary/30 dark:hover:bg-primary/15 transition-colors"
				>
					CRC Database
				</button>
			{:else}
				<section class="rounded-lg border border-primary/20 p-4 dark:border-primary/20">
					<div class="mb-3 flex items-center justify-between">
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">CRC Database</h2>
						<button
							onclick={() => (showCrcLookup = false)}
							aria-label="Close CRC database"
							class="rounded-sm p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
						>
							<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>
					<CrcLookup {job} onapply={loadJob} />
				</section>
			{/if}
		{/if}

		<!-- Rip Settings -->
		{#if job.config}
			{#if !showRipSettings}
				<button
					onclick={() => (showRipSettings = true)}
					class="rounded-lg px-3 py-1.5 text-sm font-medium bg-primary/5 text-gray-700 ring-1 ring-primary/25 hover:bg-primary/10 dark:bg-primary/10 dark:text-gray-200 dark:ring-primary/30 dark:hover:bg-primary/15 transition-colors"
				>
					Rip Settings
				</button>
			{:else}
				<section class="rounded-lg border border-primary/20 p-4 dark:border-primary/20">
					<div class="mb-3 flex items-center justify-between">
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Rip Settings</h2>
						<button
							onclick={() => (showRipSettings = false)}
							class="rounded-sm p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
							aria-label="Close rip settings"
						>
							<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>
					<RipSettings {job} config={job.config} isMusic={isMusicDisc} onsaved={handleConfigSaved} />
				</section>
			{/if}
		{/if}

		<!-- Transcode Overrides -->
		{#if isVideoDisc}
			{#if !showTranscodeOverrides}
				<button
					onclick={() => (showTranscodeOverrides = true)}
					class="rounded-lg px-3 py-1.5 text-sm font-medium bg-primary/5 text-gray-700 ring-1 ring-primary/25 hover:bg-primary/10 dark:bg-primary/10 dark:text-gray-200 dark:ring-primary/30 dark:hover:bg-primary/15 transition-colors"
				>
					Transcode Settings
				</button>
			{:else}
				<section class="rounded-lg border border-primary/20 p-4 dark:border-primary/20">
					<div class="mb-3 flex items-center justify-between">
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Transcode Settings</h2>
						<button
							onclick={() => (showTranscodeOverrides = false)}
							class="rounded-sm p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
							aria-label="Close transcode settings"
						>
							<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>
					<TranscodeOverrides {job} onsaved={loadJob} />
				</section>
			{/if}
		{/if}

		<!-- Tracks -->
		{#if job.tracks.length > 0}
			<section>
				<div class="mb-3 flex items-center justify-between">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Tracks ({job.tracks.length})</h2>
				</div>
				<div class="overflow-x-auto rounded-lg border border-primary/20 dark:border-primary/20">
					<table class="w-full text-left text-sm">
						<thead class="bg-page text-gray-600 dark:bg-primary/5 dark:text-gray-400">
							<tr>
								<th class="px-4 py-3 font-medium">#</th>
								<th class="px-4 py-3 font-medium">{isMusicDisc ? 'Title' : 'Filename'}</th>
								{#if job.multi_title && !isMusicDisc}
									<th class="px-4 py-3 font-medium">Title Override</th>
								{/if}
								<th class="px-4 py-3 font-medium">{isMusicDisc ? 'Duration' : 'Length'}</th>
								{#if isMusicDisc}
									<th class="px-4 py-3 font-medium">Format</th>
								{:else}
									<th class="px-4 py-3 font-medium">Aspect</th>
									<th class="px-4 py-3 font-medium">FPS</th>
									<th class="px-4 py-3 font-medium">Main</th>
								{/if}
								<th class="px-4 py-3 font-medium">Ripped</th>
								<th class="px-4 py-3 font-medium">Status</th>
								{#if job.multi_title && !isMusicDisc}
									<th class="px-4 py-3 font-medium"></th>
								{/if}
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
							{#each job.tracks as track}
								<tr class="hover:bg-page dark:hover:bg-gray-800/50">
									<td class="px-4 py-3">{track.track_number ?? ''}</td>
									{#if isMusicDisc}
										<td class="max-w-[300px] truncate px-4 py-3">{track.filename || track.basename || ''}</td>
									{:else}
										<td class="max-w-[200px] truncate px-4 py-3 font-mono text-xs">{track.filename ?? track.basename ?? ''}</td>
									{/if}
									{#if job.multi_title && !isMusicDisc}
										<td class="px-4 py-3">
											{#if track.title}
												<div class="flex items-center gap-1.5">
													{#if track.poster_url}
														<img src={track.poster_url} alt="" class="h-8 w-5 rounded-sm object-cover" />
													{/if}
													<div>
														<span class="font-medium text-gray-900 dark:text-white">{track.title}</span>
														{#if track.year}
															<span class="text-gray-400"> ({track.year})</span>
														{/if}
													</div>
													<span class="rounded-sm bg-purple-100 px-1 py-0.5 text-[10px] font-semibold text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">CUSTOM</span>
												</div>
											{:else}
												<span class="text-xs italic text-gray-400">(inherits job title)</span>
											{/if}
										</td>
									{/if}
									<td class="px-4 py-3">{track.length != null ? `${Math.floor(track.length / 60)}:${String(track.length % 60).padStart(2, '0')}` : ''}</td>
									{#if isMusicDisc}
										<td class="px-4 py-3 uppercase text-xs">{track.source ?? ''}</td>
									{:else}
										<td class="px-4 py-3">{track.aspect_ratio ?? ''}</td>
										<td class="px-4 py-3">{track.fps ?? ''}</td>
										<td class="px-4 py-3">{track.main_feature ? 'Yes' : ''}</td>
									{/if}
									<td class="px-4 py-3">{track.ripped ? 'Yes' : 'No'}</td>
									<td class="px-4 py-3"><StatusBadge status={track.status} /></td>
									{#if job.multi_title && !isMusicDisc}
										<td class="px-4 py-3">
											<button
												onclick={() => { editingTrackId = editingTrackId === track.track_id ? null : track.track_id; }}
												class="rounded-md px-2 py-1 text-xs font-medium text-primary hover:text-primary-hover transition-colors"
											>
												{editingTrackId === track.track_id ? 'Close' : 'Edit'}
											</button>
										</td>
									{/if}
								</tr>
								{#if job.multi_title && editingTrackId === track.track_id}
									<tr>
										<td colspan="99" class="px-4 py-3">
											<TrackTitleSearch jobId={job.job_id} {track} onapply={handleTrackTitleApply} onclose={() => { editingTrackId = null; }} />
										</td>
									</tr>
								{/if}
							{/each}
						</tbody>
					</table>
				</div>
			</section>
		{:else if isMusicDisc && musicDetailLoading}
			<section>
				<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Track Listing</h2>
				<p class="text-sm text-gray-400">Loading track listing from MusicBrainz...</p>
			</section>
		{:else if isMusicDisc && musicDetail && musicDetail.tracks.length > 0}
			<section>
				<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">
					Track Listing
					<span class="text-sm font-normal text-gray-500 dark:text-gray-400">({musicDetail.tracks.length} tracks via MusicBrainz)</span>
				</h2>
				<div class="overflow-x-auto rounded-lg border border-primary/20 dark:border-primary/20">
					<table class="w-full text-left text-sm">
						<thead class="bg-page text-gray-600 dark:bg-primary/5 dark:text-gray-400">
							<tr>
								<th class="w-12 px-4 py-3 font-medium">#</th>
								<th class="px-4 py-3 font-medium">Title</th>
								<th class="w-20 px-4 py-3 font-medium text-right">Duration</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
							{#each musicDetail.tracks as track}
								<tr class="hover:bg-page dark:hover:bg-gray-800/50">
									<td class="px-4 py-3 font-mono text-gray-500 dark:text-gray-400">{track.number}</td>
									<td class="px-4 py-3 text-gray-900 dark:text-white">{track.title}</td>
									<td class="px-4 py-3 text-right font-mono text-gray-500 dark:text-gray-400">{formatDurationMs(track.length_ms)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</section>
		{/if}

		<!-- Config -->
		{#if job.config}
			<section>
				<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Configuration</h2>
				<div class="overflow-x-auto rounded-lg border border-primary/20 dark:border-primary/20">
					<table class="w-full text-left text-sm">
						<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
							{#each Object.entries(job.config) as [key, value]}
								<tr class="hover:bg-page dark:hover:bg-gray-800/50">
									<td class="px-4 py-2 font-mono text-xs font-medium text-gray-500 dark:text-gray-400">{key}</td>
									<td class="px-4 py-2 text-gray-900 dark:text-white">{value ?? ''}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</section>
		{/if}
	</div>
{/if}
