<script lang="ts">
	import { onMount } from 'svelte';
	import type { Job, JobDetail } from '$lib/types/arm';
	import { cancelWaitingJob, startWaitingJob, fetchJob } from '$lib/api/jobs';
	import { getVideoTypeConfig } from '$lib/utils/job-type';
	import CountdownTimer from './CountdownTimer.svelte';
	import TitleSearch from './TitleSearch.svelte';
	import RipSettings from './RipSettings.svelte';

	interface Props {
		job: Job;
		paused?: boolean;
		onrefresh?: () => void;
		ondismiss?: () => void;
	}

	let { job, paused = false, onrefresh, ondismiss }: Props = $props();

	let detail = $state<JobDetail | null>(null);
	let initialLoading = $state(true);
	let showInfo = $state(false);
	let showTitleSearch = $state(false);
	let showRipSettings = $state(false);
	let cancelling = $state(false);
	let starting = $state(false);

	let waitTime = $derived(Number(detail?.config?.MANUAL_WAIT_TIME) || 60);
	let typeConfig = $derived(getVideoTypeConfig(job.video_type));
	let isVideo = $derived(
		job.disctype === 'dvd' || job.disctype === 'bluray' || job.video_type === 'movie' || job.video_type === 'series'
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
			<h3 class="truncate text-lg font-semibold text-gray-900 dark:text-white">
				{job.title || job.label || 'Untitled'}
				{#if job.year}
					<span class="font-normal text-gray-500 dark:text-gray-400">({job.year})</span>
				{/if}
			</h3>
			{#if discLabelDiffers}
				<p class="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
					Auto-detected: <span class="font-mono text-xs">{job.label}</span>
				</p>
			{/if}
			<div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500 dark:text-gray-400">
				{#if job.devpath}
					<span>{job.devpath}</span>
				{/if}
				{#if job.disctype}
					<span class="rounded bg-primary/10 px-1.5 py-0.5 capitalize dark:bg-primary/15">{job.disctype}</span>
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
					<!-- Title metadata -->
					<div class="grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
						<div>
							<span class="text-xs font-medium text-gray-500 dark:text-gray-400">Title</span>
							<p class="text-gray-900 dark:text-white">{job.title || '--'}</p>
						</div>
						<div>
							<span class="text-xs font-medium text-gray-500 dark:text-gray-400">Year</span>
							<p class="text-gray-900 dark:text-white">{job.year || '--'}</p>
						</div>
						<div>
							<span class="text-xs font-medium text-gray-500 dark:text-gray-400">Type</span>
							<p class="capitalize text-gray-900 dark:text-white">{job.video_type || '--'}</p>
						</div>
						<div>
							<span class="text-xs font-medium text-gray-500 dark:text-gray-400">Disc Type</span>
							<p class="capitalize text-gray-900 dark:text-white">{job.disctype || '--'}</p>
						</div>
						<div>
							<span class="text-xs font-medium text-gray-500 dark:text-gray-400">Disc Label</span>
							<p class="font-mono text-xs text-gray-900 dark:text-white">{job.label || '--'}</p>
						</div>
						{#if job.imdb_id}
							<div>
								<span class="text-xs font-medium text-gray-500 dark:text-gray-400">IMDb</span>
								<p><a href="https://www.imdb.com/title/{job.imdb_id}" target="_blank" rel="noopener" class="text-primary-text hover:underline dark:text-primary-text-dark">{job.imdb_id}</a></p>
							</div>
						{/if}
						<div>
							<span class="text-xs font-medium text-gray-500 dark:text-gray-400">Device</span>
							<p class="font-mono text-xs text-gray-900 dark:text-white">{job.devpath || '--'}</p>
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
					{#if job.path}
						<div class="text-sm">
							<span class="text-xs font-medium text-gray-500 dark:text-gray-400">Output Path</span>
							<p class="font-mono text-xs text-gray-700 dark:text-gray-300">{job.path}</p>
						</div>
					{/if}
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
