<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { fetchJob, retranscodeJob, fetchMusicDetail, toggleMultiTitle, updateTrack } from '$lib/api/jobs';
	import { posterSrc, posterFallback } from '$lib/utils/poster';
	import { fetchStructuredTranscoderLogContent, fetchTranscoderLogForArmJob } from '$lib/api/logs';
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
	import EpisodeMatch from '$lib/components/EpisodeMatch.svelte';
	import { formatDateTime, timeAgo, statusLabel } from '$lib/utils/format';
	import { discTypeLabel, isJobActive } from '$lib/utils/job-type';

	let job = $state<JobDetail | null>(null);
	let error = $state<string | null>(null);
	let activePanel = $state<string | null>(null);
	let showDebug = $state(false);
	let retranscoding = $state(false);
	let retranscodeFeedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);
	let transcoderLogfile = $state<string | null>(null);

	let isFolderImport = $derived(job?.source_type === 'folder');

	// MusicBrainz track listing (fetched when DB tracks are empty for music discs)
	let musicDetail = $state<MusicDetail | null>(null);
	let musicDetailLoading = $state(false);
	let togglingMultiTitle = $state(false);
	let editingTrackId = $state<number | null>(null);
	let savingTrackField = $state<string | null>(null);
	let togglingAllEnabled = $state(false);

	let minlength = $derived(Number(job?.config?.MINLENGTH) || 120);

	function isBelowMinlength(track: { length: number | null }): boolean {
		return track.length != null && track.length < minlength;
	}

	let rippableTracks = $derived(
		job?.tracks?.filter((t) => !isBelowMinlength(t)) ?? []
	);
	let allEnabled = $derived(
		!!rippableTracks.length && rippableTracks.every((t) => t.enabled)
	);

	async function handleToggleAllEnabled() {
		if (!rippableTracks.length) return;
		togglingAllEnabled = true;
		const newVal = !allEnabled;
		try {
			await Promise.all(
				rippableTracks.map((t) => updateTrack(job!.job_id, t.track_id, { enabled: newVal }))
			);
			await loadJob();
		} catch {
			// next refresh will reconcile
		} finally {
			togglingAllEnabled = false;
		}
	}

	async function handleTrackFieldUpdate(trackId: number, field: string, value: boolean | string) {
		if (!job) return;
		savingTrackField = `${trackId}-${field}`;
		try {
			await updateTrack(job.job_id, trackId, { [field]: value });
			await loadJob();
		} catch {
			// next refresh will reconcile
		} finally {
			savingTrackField = null;
		}
	}

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
		!isMusicDisc && (job?.disctype === 'dvd' || !!job?.crc_id)
	);

	function formatTvEpisodeName(track: { episode_number?: string | null; episode_name?: string | null }): string {
		if (!job || !track.episode_number) return '--';
		const pattern = job.config?.TV_TITLE_PATTERN ?? '{title} S{season}E{episode}';
		const season = String(job.season || job.season_auto || '0').padStart(2, '0');
		const episode = track.episode_number.padStart(2, '0');
		const title = job.title || job.label || '';
		const year = job.year || '';
		return pattern
			.replace(/\{title\}/gi, title)
			.replace(/\{year\}/gi, year)
			.replace(/\{season\}/gi, season)
			.replace(/\{episode\}/gi, episode)
			.replace(/\{episode_name\}/gi, track.episode_name || '')
			.replace(/\{label\}/gi, job.label || '');
	}

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
			// Look up transcoder log for this ARM job
			fetchTranscoderLogForArmJob(id).then((info) => {
				transcoderLogfile = info.found ? (info.logfile ?? null) : null;
			}).catch(() => {
				transcoderLogfile = null;
			});
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
		activePanel = null;
		loadJob();
	}

	function handleConfigSaved() {
		activePanel = null;
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
					src={posterSrc(job.poster_url)}
					alt={job.title ?? 'Poster'}
					class="rounded-lg object-cover shadow-md {isMusicDisc ? 'h-48 w-48' : 'h-64 w-44'}"
					onerror={posterFallback}
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
					<StatusBadge status={isFolderImport && job.status === 'ripping' ? 'importing' : job.status} />
					{#if job.multi_title}
						<span class="rounded-sm bg-purple-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">Multi-Title</span>
					{/if}
				</div>

				<JobActions {job} onaction={loadJob} ondelete={() => goto('/')} />

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
						<dd class="font-medium text-gray-900 dark:text-white">{statusLabel(job.status)}</dd>
					</div>
					{#if job.stage}
						<div>
							<dt class="text-gray-500 dark:text-gray-400">Stage</dt>
							<dd class="font-medium text-gray-900 dark:text-white">{job.stage}</dd>
						</div>
					{/if}
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
					{#if job.disc_number}
						<div>
							<dt class="text-gray-500 dark:text-gray-400">Disc</dt>
							<dd class="font-medium text-gray-900 dark:text-white">{job.disc_number}{#if job.disc_total} of {job.disc_total}{/if}</dd>
						</div>
					{/if}
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
					<div class="rounded-lg border p-3 text-sm {job.status === 'success'
						? 'border-yellow-200 bg-yellow-50 text-yellow-700 dark:border-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
						: 'border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400'}">
						<strong>{job.status === 'success' ? 'Warnings:' : 'Errors:'}</strong> {job.errors}
					</div>
				{/if}

				{#if job.logfile}
					<InlineLogFeed logfile={job.logfile} maxEntries={15} title="ARM Ripper Log" />
				{/if}
				{#if transcoderLogfile && !isMusicDisc && job?.disctype !== 'data'}
					<InlineLogFeed
						logfile={transcoderLogfile}
						maxEntries={15}
						title="Transcoder Log"
						fetchFn={fetchStructuredTranscoderLogContent}
						logLinkBase="/logs/transcoder"
					/>
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

		<!-- Toggle button bar -->
		<div class="flex flex-wrap gap-2">
			{#if isVideoDisc}
				<button
					onclick={() => (activePanel = activePanel === 'title' ? null : 'title')}
					class="rounded-lg px-3 py-1.5 text-sm font-medium transition-colors {activePanel === 'title' ? 'bg-indigo-200 text-indigo-800 dark:bg-indigo-800/50 dark:text-indigo-300' : 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 dark:hover:bg-indigo-900/50'}"
				>
					Identify
				</button>
			{/if}
			{#if isMusicDisc}
				<button
					onclick={() => (activePanel = activePanel === 'music' ? null : 'music')}
					class="rounded-lg px-3 py-1.5 text-sm font-medium transition-colors {activePanel === 'music' ? 'bg-indigo-200 text-indigo-800 dark:bg-indigo-800/50 dark:text-indigo-300' : 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 dark:hover:bg-indigo-900/50'}"
				>
					Search Music
				</button>
			{/if}
			{#if hasCrcData}
				<button
					onclick={() => (activePanel = activePanel === 'crc' ? null : 'crc')}
					class="rounded-lg px-3 py-1.5 text-sm font-medium transition-colors {activePanel === 'crc' ? 'bg-primary/15 text-gray-900 ring-1 ring-primary/40 dark:bg-primary/20 dark:text-white dark:ring-primary/40' : 'bg-primary/5 text-gray-700 ring-1 ring-primary/25 hover:bg-primary/10 dark:bg-primary/10 dark:text-gray-200 dark:ring-primary/30 dark:hover:bg-primary/15'}"
				>
					CRC Database
				</button>
			{/if}
			{#if job.config}
				<button
					onclick={() => (activePanel = activePanel === 'rip' ? null : 'rip')}
					class="rounded-lg px-3 py-1.5 text-sm font-medium transition-colors {activePanel === 'rip' ? 'bg-primary/15 text-gray-900 ring-1 ring-primary/40 dark:bg-primary/20 dark:text-white dark:ring-primary/40' : 'bg-primary/5 text-gray-700 ring-1 ring-primary/25 hover:bg-primary/10 dark:bg-primary/10 dark:text-gray-200 dark:ring-primary/30 dark:hover:bg-primary/15'}"
				>
					Rip Settings
				</button>
			{/if}
			{#if isVideoDisc && (job.video_type === 'series' || job.imdb_id)}
				<button
					onclick={() => (activePanel = activePanel === 'tvdb' ? null : 'tvdb')}
					class="rounded-lg px-3 py-1.5 text-sm font-medium transition-colors {activePanel === 'tvdb' ? 'bg-blue-200 text-blue-800 dark:bg-blue-800/50 dark:text-blue-300' : 'bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:hover:bg-blue-900/50'}"
				>
					Episodes
				</button>
			{/if}
			{#if isVideoDisc}
				<button
					onclick={() => (activePanel = activePanel === 'transcode' ? null : 'transcode')}
					class="rounded-lg px-3 py-1.5 text-sm font-medium transition-colors {activePanel === 'transcode' ? 'bg-primary/15 text-gray-900 ring-1 ring-primary/40 dark:bg-primary/20 dark:text-white dark:ring-primary/40' : 'bg-primary/5 text-gray-700 ring-1 ring-primary/25 hover:bg-primary/10 dark:bg-primary/10 dark:text-gray-200 dark:ring-primary/30 dark:hover:bg-primary/15'}"
				>
					Transcode Settings
				</button>
			{/if}
		</div>

		<!-- Active panel content -->
		{#if activePanel === 'title'}
			<section class="rounded-lg border border-primary/20 p-4 dark:border-primary/20">
				<TitleSearch {job} onapply={handleTitleApply} />
			</section>
		{:else if activePanel === 'music'}
			<section class="rounded-lg border border-primary/20 p-4 dark:border-primary/20">
				<MusicSearch {job} onapply={handleTitleApply} />
			</section>
		{:else if activePanel === 'crc'}
			<section class="rounded-lg border border-primary/20 p-4 dark:border-primary/20">
				<CrcLookup {job} onapply={loadJob} />
			</section>
		{:else if activePanel === 'rip'}
			<section class="rounded-lg border border-primary/20 p-4 dark:border-primary/20">
				<RipSettings {job} config={job.config!} isMusic={isMusicDisc} multiTitle={!!job.multi_title} onsaved={handleConfigSaved} />
			</section>
		{:else if activePanel === 'tvdb'}
			<section class="rounded-lg border border-primary/20 p-4 dark:border-primary/20">
				<EpisodeMatch {job} onapply={loadJob} />
			</section>
		{:else if activePanel === 'transcode'}
			<section class="rounded-lg border border-primary/20 p-4 dark:border-primary/20">
				<TranscodeOverrides {job} onsaved={loadJob} />
			</section>
		{/if}

		<!-- Tracks -->
		{#if job.tracks.length > 0}
			<section>
				<div class="mb-3 flex items-center justify-between">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white">
						Tracks ({job.tracks.length})
						{#if job.disc_number && job.disc_total}
							<span class="text-sm font-normal text-gray-500 dark:text-gray-400">— Disc {job.disc_number} of {job.disc_total}</span>
						{/if}
					</h2>
				</div>
				<div class="overflow-x-auto rounded-lg border border-primary/20 dark:border-primary/20">
					<table class="w-full text-left text-sm">
						<thead class="bg-page text-gray-600 dark:bg-primary/5 dark:text-gray-400">
							<tr>
								<th class="px-4 py-3 font-medium">#</th>
								<th class="px-4 py-3 font-medium">{isMusicDisc ? 'Name' : 'Filename'}</th>
								{#if !isMusicDisc}
									<th class="px-4 py-3 font-medium">Title Override</th>
								{/if}
								{#if !isMusicDisc && job.video_type === 'series'}
									<th class="px-4 py-3 font-medium">Episode</th>
								{/if}
								<th class="px-4 py-3 font-medium">{isMusicDisc ? 'Duration' : 'Length'}</th>
								{#if !isMusicDisc}
									<th class="px-4 py-3 font-medium">Aspect</th>
									<th class="px-4 py-3 font-medium">FPS</th>
									<th class="pl-1 pr-4 py-3 font-medium">
										<label class="flex items-center gap-1.5 cursor-pointer">
											<span>Rip</span>
											<input
												type="checkbox"
												checked={allEnabled}
												onchange={handleToggleAllEnabled}
												disabled={togglingAllEnabled}
												class="h-4 w-4 rounded-sm border-primary/25 text-primary focus:ring-primary dark:border-primary/30 dark:bg-primary/10"
											/>
										</label>
									</th>
								{/if}
								<th class="px-4 py-3 font-medium">Ripped</th>
								<th class="px-4 py-3 font-medium">Status</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
							{#each job.tracks as track}
								{@const tooShort = !isMusicDisc && isBelowMinlength(track)}
								<tr class="{tooShort ? 'opacity-40' : ''} hover:bg-page dark:hover:bg-gray-800/50">
									<td class="px-4 py-3">{track.track_number ?? ''}</td>
									{#if isMusicDisc}
										<td class="max-w-[300px] truncate px-4 py-3">{track.title || track.filename || '--'}</td>
									{:else}
										<td class="max-w-[250px] truncate px-4 py-3 font-mono text-xs text-gray-700 dark:text-gray-300">{track.filename ?? track.basename ?? '--'}</td>
									{/if}
									{#if !isMusicDisc}
										<td
											class="px-4 py-3 cursor-pointer hover:bg-primary/5 dark:hover:bg-primary/10"
											onclick={() => { editingTrackId = editingTrackId === track.track_id ? null : track.track_id; }}
										>
											{#if track.title}
												<div class="flex items-center gap-1.5">
													{#if track.poster_url}
														<img src={posterSrc(track.poster_url)} alt="" class="h-8 w-5 rounded-sm object-cover" onerror={posterFallback} />
													{/if}
													<div>
														<span class="font-medium text-gray-900 dark:text-white">{track.title}</span>
														{#if track.year}
															<span class="text-gray-400"> ({track.year})</span>
														{/if}
													</div>
												</div>
											{:else}
												<span class="text-xs text-gray-400">{job.title || job.label || 'Untitled'}{#if job.year} ({job.year}){/if}</span>
											{/if}
										</td>
									{/if}
									{#if !isMusicDisc && job.video_type === 'series'}
									<td class="px-4 py-3">
										{#if track.episode_number}
											<span class="font-medium text-blue-700 dark:text-blue-400">
												{formatTvEpisodeName(track)}
											</span>
											{#if track.episode_name}
												<span class="ml-1 text-xs text-gray-500 dark:text-gray-400">{track.episode_name}</span>
											{/if}
										{:else}
											<span class="text-xs text-gray-400">--</span>
										{/if}
									</td>
								{/if}
								<td class="px-4 py-3">{track.length != null ? `${Math.floor(track.length / 60)}:${String(track.length % 60).padStart(2, '0')}` : ''}</td>
									{#if !isMusicDisc}
										<td class="px-4 py-3">{track.aspect_ratio ?? ''}</td>
										<td class="px-4 py-3">{track.fps ?? ''}</td>
										<td class="pl-1 pr-4 py-3">
											{#if tooShort}
												<span class="ml-4 text-[10px] text-gray-400 dark:text-gray-500" title="Too short to rip (below {minlength}s minimum)">skip</span>
											{:else}
												<input
													type="checkbox"
													checked={track.enabled}
													onchange={() => handleTrackFieldUpdate(track.track_id, 'enabled', !track.enabled)}
													disabled={savingTrackField === `${track.track_id}-enabled`}
													class="ml-[26px] h-4 w-4 rounded-sm border-primary/25 text-primary focus:ring-primary disabled:opacity-50 dark:border-primary/30 dark:bg-primary/10"
												/>
											{/if}
										</td>
									{/if}
									<td class="px-4 py-3">
										<span class="rounded-sm px-1.5 py-0.5 text-[10px] font-semibold {track.ripped
											? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
											: 'bg-gray-100 text-gray-400 dark:bg-gray-700/50 dark:text-gray-500'}"
										>
											{track.ripped ? 'Yes' : 'No'}
										</span>
									</td>
									<td class="px-4 py-3"><StatusBadge status={track.status} /></td>
									</tr>
								{#if editingTrackId === track.track_id}
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

		<!-- Debug -->
		{#if job.config}
			<section>
				<button
					onclick={() => { showDebug = !showDebug; }}
					class="flex w-full items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white"
				>
					<svg class="h-4 w-4 transition-transform {showDebug ? 'rotate-90' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
					</svg>
					Debug
				</button>
				{#if showDebug}
					<div class="mt-3 overflow-x-auto rounded-lg border border-primary/20 dark:border-primary/20">
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
				{/if}
			</section>
		{/if}
	</div>
{/if}
