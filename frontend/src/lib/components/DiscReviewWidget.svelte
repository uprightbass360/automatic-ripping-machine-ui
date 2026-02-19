<script lang="ts">
	import { onMount } from 'svelte';
	import type { Job, JobDetail } from '$lib/types/arm';
	import { cancelWaitingJob, startWaitingJob, fetchJob, updateJobTitle } from '$lib/api/jobs';
	import { getVideoTypeConfig, discTypeLabel } from '$lib/utils/job-type';
	import CountdownTimer from './CountdownTimer.svelte';
	import TitleSearch from './TitleSearch.svelte';
	import RipSettings from './RipSettings.svelte';
	import DiscTypeIcon from './DiscTypeIcon.svelte';

	interface Props {
		job: Job;
		driveNames?: Record<string, string>;
		paused?: boolean;
		onrefresh?: () => void;
		ondismiss?: () => void;
	}

	let { job, driveNames = {}, paused = false, onrefresh, ondismiss }: Props = $props();
	let driveName = $derived(job.devpath ? driveNames[job.devpath] : null);

	let detail = $state<JobDetail | null>(null);
	let initialLoading = $state(true);
	let showInfo = $state(false);
	let showTitleSearch = $state(false);
	let showRipSettings = $state(false);
	let cancelling = $state(false);
	let starting = $state(false);

	// Editable metadata in Disc Info panel
	let infoTitle = $state(job.title || '');
	let infoYear = $state(job.year || '');
	let infoType = $state(job.video_type || '');
	let infoImdbId = $state(job.imdb_id || '');
	let infoPosterUrl = $state(job.poster_url || '');
	let infoPath = $state(job.path || '');
	let infoSaving = $state(false);
	let infoFeedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);

	let infoDirty = $derived(
		infoTitle !== (job.title || '') ||
		infoYear !== (job.year || '') ||
		infoType !== (job.video_type || '') ||
		infoImdbId !== (job.imdb_id || '') ||
		infoPosterUrl !== (job.poster_url || '') ||
		infoPath !== (job.path || '')
	);

	async function saveInfo() {
		infoSaving = true;
		infoFeedback = null;
		try {
			await updateJobTitle(job.job_id, {
				title: infoTitle.trim() || undefined,
				year: infoYear.trim() || undefined,
				video_type: infoType || undefined,
				imdb_id: infoImdbId.trim() || undefined,
				poster_url: infoPosterUrl.trim() || undefined,
				path: infoPath.trim() || undefined,
			});
			infoFeedback = { type: 'success', message: 'Saved' };
			onrefresh?.();
		} catch (e) {
			infoFeedback = { type: 'error', message: e instanceof Error ? e.message : 'Save failed' };
		} finally {
			infoSaving = false;
		}
	}

	let waitTime = $derived(Number(detail?.config?.MANUAL_WAIT_TIME) || 60);
	let typeConfig = $derived(getVideoTypeConfig(job.video_type));
	let isVideo = $derived(
		job.disctype === 'dvd' || job.disctype === 'bluray' || job.disctype === 'bluray4k' || job.video_type === 'movie' || job.video_type === 'series'
	);
	let discLabelDiffers = $derived(
		!!job.label && !!job.title && job.label.toLowerCase() !== job.title.toLowerCase()
	);

	async function loadDetail() {
		try {
			detail = await fetchJob(job.job_id);
		} catch {
			detail = null;
		} finally {
			initialLoading = false;
		}
	}

	function handleTitleApply() {
		onrefresh?.();
		loadDetail();
	}

	function handleConfigSaved() {
		onrefresh?.();
		loadDetail();
	}

	async function handleStart() {
		starting = true;
		try {
			await startWaitingJob(job.job_id);
		} catch {
			// next refresh will reconcile
		} finally {
			starting = false;
			ondismiss?.();
			onrefresh?.();
		}
	}

	async function handleCancel() {
		cancelling = true;
		try {
			await cancelWaitingJob(job.job_id);
		} catch {
			// still dismiss — next refresh will reconcile
		} finally {
			cancelling = false;
			ondismiss?.();
			onrefresh?.();
		}
	}

	function toggleSection(section: 'info' | 'title' | 'settings') {
		if (section === 'info') {
			showInfo = !showInfo;
			if (showInfo) { showTitleSearch = false; showRipSettings = false; }
		} else if (section === 'title') {
			showTitleSearch = !showTitleSearch;
			if (showTitleSearch) { showInfo = false; showRipSettings = false; }
		} else {
			showRipSettings = !showRipSettings;
			if (showRipSettings) { showInfo = false; showTitleSearch = false; }
		}
	}

	function formatLength(secs: number | null): string {
		if (!secs) return '--';
		const h = Math.floor(secs / 3600);
		const m = Math.floor((secs % 3600) / 60);
		const s = secs % 60;
		if (h > 0) return `${h}h ${m}m ${s}s`;
		return `${m}m ${s}s`;
	}

	onMount(() => {
		loadDetail();
	});

	const btnBase =
		'rounded-lg px-3 py-1.5 text-sm font-medium transition-colors';
</script>

<div class="overflow-hidden rounded-lg border-2 border-primary bg-surface shadow-md dark:border-primary dark:bg-surface-dark">
	<!-- Status bar -->
	<div class="flex items-center justify-between bg-primary px-4 py-1.5 dark:bg-primary-dark">
		<div class="flex items-center gap-2">
			<div class="h-2 w-2 animate-pulse rounded-full bg-white/80"></div>
			<span class="text-sm font-semibold text-on-primary">Waiting for Review</span>
		</div>
		{#if job.start_time}
			<CountdownTimer startTime={job.start_time} waitSeconds={waitTime} {paused} inverted />
		{/if}
	</div>

	<!-- Header -->
	<div class="flex gap-4 p-4">
		<!-- Poster -->
		{#if job.poster_url}
			<img
				src={job.poster_url}
				alt={job.title ?? 'Poster'}
				class="h-24 w-16 flex-shrink-0 rounded object-cover"
			/>
		{:else}
			<div class="flex h-24 w-16 flex-shrink-0 items-center justify-center rounded {typeConfig.placeholderClasses}">
				<svg class="h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
					<circle cx="12" cy="12" r="10" />
					<circle cx="12" cy="12" r="3" />
					<circle cx="12" cy="12" r="6.5" stroke-width="0.75" opacity="0.4" />
				</svg>
			</div>
		{/if}

		<!-- Info -->
		<div class="min-w-0 flex-1">
			<div class="flex flex-wrap items-center gap-2">
				<h3 class="truncate text-lg font-semibold text-gray-900 dark:text-white">
					{job.title || job.label || 'Untitled'}
					{#if job.year}
						<span class="font-normal text-gray-500 dark:text-gray-400">({job.year})</span>
					{/if}
				</h3>
				{#if job.imdb_id}
					<a
						href="https://www.imdb.com/title/{job.imdb_id}/"
						target="_blank"
						rel="noopener noreferrer"
						class="inline-flex items-center rounded bg-yellow-400 px-1.5 py-0.5 text-xs font-bold text-black hover:bg-yellow-300"
					>IMDb</a>
				{/if}
			</div>
			{#if discLabelDiffers}
				<p class="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
					Auto-detected: <span class="font-mono text-xs">{job.label}</span>
				</p>
			{/if}
			<div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500 dark:text-gray-400">
				{#if job.devpath}
					<span>{driveName ?? job.devpath}</span>
				{/if}
				{#if job.disctype}
					<span class="rounded bg-primary/10 px-1.5 py-0.5 dark:bg-primary/15">{discTypeLabel(job.disctype)}</span>
				{/if}
			</div>
		</div>
	</div>

	<!-- Action buttons -->
	<div class="flex items-center gap-2 border-t border-primary/20 bg-primary-light-bg/50 px-4 py-2 dark:border-primary/20 dark:bg-primary-light-bg-dark/10">
		<button
			onclick={() => toggleSection('info')}
			class="{btnBase} {showInfo
				? 'bg-primary text-on-primary'
				: 'bg-primary/5 text-gray-700 ring-1 ring-primary/25 hover:bg-primary/10 dark:bg-primary/10 dark:text-gray-200 dark:ring-primary/30 dark:hover:bg-primary/15'}"
		>
			Disc Info
		</button>
		{#if isVideo}
			<button
				onclick={() => toggleSection('title')}
				class="{btnBase} {showTitleSearch
					? 'bg-primary text-on-primary'
					: 'bg-primary/5 text-gray-700 ring-1 ring-primary/25 hover:bg-primary/10 dark:bg-primary/10 dark:text-gray-200 dark:ring-primary/30 dark:hover:bg-primary/15'}"
			>
				Search/Edit Title
			</button>
		{/if}
		<button
			onclick={() => toggleSection('settings')}
			class="{btnBase} {showRipSettings
				? 'bg-primary text-on-primary'
				: 'bg-primary/5 text-gray-700 ring-1 ring-primary/25 hover:bg-primary/10 dark:bg-primary/10 dark:text-gray-200 dark:ring-primary/30 dark:hover:bg-primary/15'}"
		>
			Rip Settings
		</button>
		<button
			onclick={handleStart}
			disabled={starting}
			class="{btnBase} ml-auto bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 dark:bg-emerald-700 dark:hover:bg-emerald-600"
		>
			{starting ? 'Starting...' : 'Start Ripping'}
		</button>
		<button
			onclick={handleCancel}
			disabled={cancelling}
			class="{btnBase} text-red-600 ring-1 ring-red-300 hover:bg-red-50 disabled:opacity-50 dark:text-red-400 dark:ring-red-700 dark:hover:bg-red-900/20"
		>
			{cancelling ? 'Cancelling...' : 'Cancel'}
		</button>
	</div>

	<!-- Expanded sections -->
	{#if showInfo}
		<div class="border-t border-primary/20 p-4 dark:border-primary/20">
			{#if initialLoading}
				<p class="text-sm text-gray-400">Loading...</p>
			{:else}
				<div class="space-y-4">
					<!-- Auto-detection context -->
					{#if job.title_auto}
						<div class="flex items-center gap-2 rounded-md bg-primary/5 px-3 py-2 text-xs dark:bg-primary/10">
							<span class="text-gray-500 dark:text-gray-400">Auto-detected:</span>
							<span class="font-medium text-gray-700 dark:text-gray-300">{job.title_auto}{#if job.year_auto} ({job.year_auto}){/if}</span>
							{#if job.hasnicetitle}
								<span class="rounded bg-green-100 px-1.5 py-0.5 font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">confident</span>
							{:else}
								<span class="rounded bg-amber-100 px-1.5 py-0.5 font-medium text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">best guess</span>
							{/if}
						</div>
					{/if}

					<!-- Editable metadata -->
					<div class="space-y-2">
						<label class="block">
							<span class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Title</span>
							<input type="text" bind:value={infoTitle} class="w-full rounded border border-primary/25 bg-primary/5 px-2 py-1 text-sm text-gray-900 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white" />
						</label>
						<div class="grid grid-cols-3 gap-3">
							<label>
								<span class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Year</span>
								<input type="text" bind:value={infoYear} class="w-full rounded border border-primary/25 bg-primary/5 px-2 py-1 text-sm text-gray-900 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white" />
							</label>
							<label>
								<span class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Type</span>
								<select bind:value={infoType} class="w-full rounded border border-primary/25 bg-primary/5 px-2 py-1 text-sm text-gray-900 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white">
									<option value="movie">Movie</option>
									<option value="series">Series</option>
								</select>
							</label>
							<label>
								<span class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">IMDb ID</span>
								<input type="text" bind:value={infoImdbId} placeholder="tt..." class="w-full rounded border border-primary/25 bg-primary/5 px-2 py-1 text-sm text-gray-900 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white" />
							</label>
						</div>
						<label class="block">
							<span class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Poster URL</span>
							<input type="text" bind:value={infoPosterUrl} placeholder="https://..." class="w-full rounded border border-primary/25 bg-primary/5 px-2 py-1 text-sm text-gray-900 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white" />
						</label>
					</div>

					{#if infoDirty}
						<div class="flex items-center gap-2">
							<button
								onclick={saveInfo}
								disabled={infoSaving}
								class="{btnBase} bg-primary text-on-primary hover:bg-primary-hover disabled:opacity-50"
							>
								{infoSaving ? 'Saving...' : 'Save'}
							</button>
							{#if infoFeedback}
								<span class="text-xs {infoFeedback.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
									{infoFeedback.message}
								</span>
							{/if}
						</div>
					{/if}

					<!-- Read-only disc details -->
					<div class="grid grid-cols-5 gap-3 text-sm">
						<div>
							<span class="text-xs font-medium text-gray-500 dark:text-gray-400">Disc Type</span>
							<p class="flex items-center gap-1.5 text-gray-900 dark:text-white">
								<DiscTypeIcon disctype={job.disctype} size="h-5 w-5" />
								<span>{discTypeLabel(job.disctype) || '--'}</span>
							</p>
						</div>
						<div>
							<span class="text-xs font-medium text-gray-500 dark:text-gray-400">Disc Label</span>
							<p class="font-mono text-xs text-gray-900 dark:text-white">{job.label || '--'}</p>
						</div>
						<div>
							<span class="text-xs font-medium text-gray-500 dark:text-gray-400">Drive</span>
							<p class="text-gray-900 dark:text-white">{driveName ?? job.devpath ?? '--'}</p>
						</div>
						<div>
							<span class="text-xs font-medium text-gray-500 dark:text-gray-400">CRC</span>
							<p class="font-mono text-xs text-gray-900 dark:text-white">{job.crc_id || '--'}</p>
						</div>
						<div>
							<span class="text-xs font-medium text-gray-500 dark:text-gray-400">Titles on Disc</span>
							<p class="text-gray-900 dark:text-white">{job.no_of_titles ?? '--'}</p>
						</div>
					</div>

					<!-- Tracks table -->
					{#if detail?.tracks && detail.tracks.length > 0}
						<div>
							<h4 class="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-300">Tracks ({detail.tracks.length})</h4>
							<div class="overflow-x-auto rounded-md border border-primary/15 dark:border-primary/20">
								<table class="w-full text-left text-xs">
									<thead class="bg-page text-gray-500 dark:bg-primary/5 dark:text-gray-400">
										<tr>
											<th class="px-3 py-1.5 font-medium">#</th>
											<th class="px-3 py-1.5 font-medium">Length</th>
											<th class="px-3 py-1.5 font-medium">Aspect</th>
											<th class="px-3 py-1.5 font-medium">FPS</th>
											<th class="px-3 py-1.5 font-medium">Main</th>
											<th class="px-3 py-1.5 font-medium">File</th>
										</tr>
									</thead>
									<tbody class="divide-y divide-gray-100 dark:divide-gray-700/50">
										{#each detail.tracks as track}
											<tr class="{track.main_feature ? 'bg-primary-light-bg/50 dark:bg-primary-light-bg-dark/10' : ''}">
												<td class="px-3 py-1.5 font-mono text-gray-700 dark:text-gray-300">{track.track_number ?? '--'}</td>
												<td class="px-3 py-1.5 text-gray-700 dark:text-gray-300">{formatLength(track.length)}</td>
												<td class="px-3 py-1.5 text-gray-500 dark:text-gray-400">{track.aspect_ratio ?? '--'}</td>
												<td class="px-3 py-1.5 text-gray-500 dark:text-gray-400">{track.fps ?? '--'}</td>
												<td class="px-3 py-1.5">
													{#if track.main_feature}
														<span class="rounded bg-primary/15 px-1.5 py-0.5 text-[10px] font-semibold text-primary-text dark:bg-primary/20 dark:text-primary-text-dark">MAIN</span>
													{/if}
												</td>
												<td class="px-3 py-1.5 font-mono text-gray-500 dark:text-gray-400">{track.filename ?? track.basename ?? '--'}</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						</div>
					{/if}

					<!-- Output path -->
					<label class="block text-sm">
						<span class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Output Path</span>
						<input type="text" bind:value={infoPath} class="w-full rounded border border-primary/25 bg-primary/5 px-2 py-1 font-mono text-xs text-gray-900 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white" />
					</label>
				</div>
			{/if}
		</div>
	{/if}

	{#if showTitleSearch && isVideo}
		<div class="border-t border-primary/20 p-4 dark:border-primary/20">
			<TitleSearch {job} onapply={handleTitleApply} />
		</div>
	{/if}

	{#if showRipSettings && detail?.config}
		<div class="border-t border-primary/20 p-4 dark:border-primary/20">
			<RipSettings {job} config={detail.config} onsaved={handleConfigSaved} />
		</div>
	{:else if showRipSettings && initialLoading}
		<div class="border-t border-primary/20 p-4 text-sm text-gray-400 dark:border-primary/20">
			Loading config...
		</div>
	{/if}
</div>
