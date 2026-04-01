<script lang="ts">
	import type { Job } from '$lib/types/arm';
	import StatusBadge from './StatusBadge.svelte';
	import ProgressBar from './ProgressBar.svelte';
	import { elapsedTime } from '$lib/utils/format';
	import { getVideoTypeConfig, isJobActive, discTypeLabel } from '$lib/utils/job-type';
	import DiscTypeIcon from './DiscTypeIcon.svelte';
	import TimeAgo from './TimeAgo.svelte';
	import { posterSrc } from '$lib/utils/poster';
	import { slide } from 'svelte/transition';

	interface Props {
		job: Job;
		driveNames?: Record<string, string>;
		progress?: number | null;
		progressStage?: string | null;
	}

	let { job, driveNames = {}, progress = null, progressStage = null }: Props = $props();
	let expanded = $state(false);

	let driveName = $derived(job.devpath ? driveNames[job.devpath] : null);
	let typeConfig = $derived(getVideoTypeConfig(job.video_type));
	let active = $derived(isJobActive(job.status));
	let hasErrors = $derived(!!job.errors && job.errors.trim().length > 0);
	let isFolderImport = $derived(job.source_type === 'folder');
	let discLabelDiffers = $derived(
		!!job.label && !!job.title && job.label.toLowerCase() !== job.title.toLowerCase()
	);

	function toggle(e: MouseEvent) {
		// Don't toggle when clicking links/buttons inside
		if ((e.target as HTMLElement).closest('a, button:not(.row-toggle)')) return;
		expanded = !expanded;
	}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
<div
	class="rounded-lg border border-primary/20 border-l-4 {typeConfig.accentBorder} bg-surface shadow-xs transition dark:border-primary/20 dark:bg-surface-dark"
	onclick={toggle}
	role="button"
	tabindex="0"
>
	<!-- Collapsed row -->
	<div class="flex items-center gap-3 px-4 py-2.5 cursor-pointer">
		<!-- Poster thumbnail -->
		{#if job.poster_url}
			<img src={posterSrc(job.poster_url)} alt="" class="h-10 w-7 shrink-0 rounded-sm object-cover" />
		{:else}
			<div class="flex h-10 w-7 shrink-0 items-center justify-center rounded-sm {typeConfig.placeholderClasses}">
				<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
					<circle cx="12" cy="12" r="10" />
					<circle cx="12" cy="12" r="3" />
				</svg>
			</div>
		{/if}

		<!-- Title -->
		<h3 class="min-w-0 flex-shrink truncate font-semibold text-sm text-gray-900 dark:text-white">
			{job.title || job.label || 'Untitled'}
		</h3>

		<!-- Year -->
		{#if job.year}
			<span class="shrink-0 text-xs text-gray-500 dark:text-gray-400">{job.year}</span>
		{/if}

		<!-- Status badge -->
		<div class="shrink-0">
			<StatusBadge status={isFolderImport && job.status === 'ripping' ? 'importing' : job.status} />
		</div>

		<!-- Type + disc badges -->
		<div class="hidden sm:flex shrink-0 items-center gap-1.5">
			<span class="rounded-sm px-1.5 py-0.5 text-xs font-medium {typeConfig.badgeClasses}">{typeConfig.label}</span>
			{#if job.disctype}
				<span class="inline-flex items-center gap-0.5 rounded-sm bg-primary/10 px-1.5 py-0.5 text-xs dark:bg-primary/15">
					<DiscTypeIcon disctype={job.disctype} size="h-3 w-3" />
					{discTypeLabel(job.disctype)}
				</span>
			{/if}
		</div>

		<!-- Drive / source -->
		<span class="hidden md:inline shrink-0 text-xs text-gray-500 dark:text-gray-400">
			{#if job.devpath}
				{driveName ?? job.devpath}
			{:else if job.source_path}
				{job.source_path.split('/').slice(-1)[0]}
			{/if}
		</span>

		<!-- Progress bar (inline) -->
		{#if active}
			<div class="hidden lg:block flex-1 min-w-24 max-w-48">
				{#if progress != null && progress > 0}
					<ProgressBar value={progress} color="bg-primary" />
				{:else}
					<div class="h-2 overflow-hidden rounded-full bg-primary/15">
						<div class="h-full w-1/3 animate-indeterminate rounded-full bg-primary/60"></div>
					</div>
				{/if}
			</div>
		{/if}

		<!-- Track counts -->
		{#if active && job.tracks_total != null && job.tracks_total > 0 && !isFolderImport}
			<span class="hidden lg:inline shrink-0 text-xs text-gray-500 dark:text-gray-400">
				{job.tracks_ripped ?? 0}/{job.tracks_total}
			</span>
		{/if}

		<!-- Elapsed -->
		{#if active && job.start_time}
			<span class="shrink-0 text-xs text-gray-500 dark:text-gray-400">{elapsedTime(job.start_time)}</span>
		{/if}

		<!-- Errors indicator -->
		{#if hasErrors}
			<span class="shrink-0 text-red-500 dark:text-red-400" title={job.errors ?? ''}>
				<svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
					<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
				</svg>
			</span>
		{/if}

		<!-- Expand chevron -->
		<button class="row-toggle shrink-0 p-0.5 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-transform" class:rotate-180={expanded} title={expanded ? 'Collapse' : 'Expand'}>
			<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
			</svg>
		</button>
	</div>

	<!-- Mobile progress (below collapsed row) -->
	{#if active && !expanded}
		<div class="lg:hidden px-4 pb-2.5">
			{#if progress != null && progress > 0}
				<ProgressBar value={progress} color="bg-primary" />
			{:else}
				<div class="h-2 overflow-hidden rounded-full bg-primary/15">
					<div class="h-full w-1/3 animate-indeterminate rounded-full bg-primary/60"></div>
				</div>
			{/if}
		</div>
	{/if}

	<!-- Expanded detail -->
	{#if expanded}
		<div transition:slide={{ duration: 200 }} class="border-t border-primary/10 px-4 py-3 dark:border-primary/15">
			<div class="flex gap-4">
				<!-- Poster (larger) -->
				{#if job.poster_url}
					<img src={posterSrc(job.poster_url)} alt={job.title ?? 'Poster'} class="h-28 w-20 shrink-0 rounded-sm object-cover" />
				{/if}

				<div class="min-w-0 flex-1 space-y-2">
					<!-- Title row -->
					<div class="flex items-start justify-between gap-2">
						<a href="/jobs/{job.job_id}" class="text-sm font-semibold text-primary hover:underline">{job.title || job.label || 'Untitled'}</a>
						{#if job.imdb_id}
							<a
								href="https://www.imdb.com/title/{job.imdb_id}/"
								target="_blank"
								rel="noopener noreferrer"
								class="inline-flex items-center rounded-sm bg-yellow-400 px-1.5 py-0.5 text-xs font-bold text-black hover:bg-yellow-300"
							>IMDb</a>
						{/if}
					</div>

					<!-- Metadata grid -->
					<dl class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-xs">
						{#if job.year}
							<dt class="text-gray-500 dark:text-gray-400">Year</dt>
							<dd class="text-gray-900 dark:text-white">{job.year}</dd>
						{/if}
						<dt class="text-gray-500 dark:text-gray-400">Type</dt>
						<dd><span class="rounded-sm px-1 py-0.5 font-medium {typeConfig.badgeClasses}">{typeConfig.label}</span></dd>
						{#if job.disctype}
							<dt class="text-gray-500 dark:text-gray-400">Disc</dt>
							<dd class="inline-flex items-center gap-1">
								<DiscTypeIcon disctype={job.disctype} size="h-3.5 w-3.5" />
								{discTypeLabel(job.disctype)}
							</dd>
						{/if}
						{#if job.disc_number}
							<dt class="text-gray-500 dark:text-gray-400">Disc #</dt>
							<dd>{job.disc_number}{#if job.disc_total} / {job.disc_total}{/if}</dd>
						{/if}
						{#if discLabelDiffers}
							<dt class="text-gray-500 dark:text-gray-400">Label</dt>
							<dd class="font-mono text-gray-600 dark:text-gray-400">{job.label}</dd>
						{/if}
						{#if job.devpath}
							<dt class="text-gray-500 dark:text-gray-400">Drive</dt>
							<dd>{driveName ?? job.devpath}</dd>
						{:else if job.source_path}
							<dt class="text-gray-500 dark:text-gray-400">Source</dt>
							<dd class="truncate" title={job.source_path}>{job.source_path}</dd>
						{/if}
						{#if isFolderImport}
							<dt class="text-gray-500 dark:text-gray-400">Mode</dt>
							<dd class="inline-flex items-center gap-1 text-violet-600 dark:text-violet-400">
								<svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
								</svg>
								Folder Import
							</dd>
						{/if}
						{#if job.stage}
							<dt class="text-gray-500 dark:text-gray-400">Stage</dt>
							<dd><span class="rounded-sm bg-primary-light-bg px-1.5 py-0.5 font-medium text-primary-text dark:bg-primary-light-bg-dark/20 dark:text-primary-text-dark">{job.stage}</span></dd>
						{/if}
						{#if !isFolderImport && job.tracks_total != null && job.tracks_total > 0}
							<dt class="text-gray-500 dark:text-gray-400">Tracks</dt>
							<dd>{job.tracks_ripped ?? 0} / {job.tracks_total} ripped</dd>
						{:else if job.no_of_titles != null}
							<dt class="text-gray-500 dark:text-gray-400">Titles</dt>
							<dd>{job.no_of_titles}</dd>
						{/if}
						{#if job.start_time}
							<dt class="text-gray-500 dark:text-gray-400">Started</dt>
							<dd><TimeAgo date={job.start_time} /></dd>
						{/if}
						{#if !active && job.stop_time}
							<dt class="text-gray-500 dark:text-gray-400">Finished</dt>
							<dd><TimeAgo date={job.stop_time} /></dd>
						{/if}
						{#if !active && job.job_length}
							<dt class="text-gray-500 dark:text-gray-400">Duration</dt>
							<dd>{job.job_length}</dd>
						{/if}
					</dl>

					<!-- Errors -->
					{#if hasErrors}
						<div class="flex items-center gap-1 text-xs text-red-500 dark:text-red-400">
							<svg class="h-3.5 w-3.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
							</svg>
							{#if job.logfile}
								<a href="/logs/{job.logfile}" class="hover:underline">{job.errors}</a>
							{:else}
								<span>{job.errors}</span>
							{/if}
						</div>
					{/if}

					<!-- Progress (expanded) -->
					{#if active}
						<div>
							{#if progress != null && progress > 0}
								<ProgressBar value={progress} color="bg-primary" />
								{#if progressStage}
									<p class="mt-0.5 text-xs text-gray-400 dark:text-gray-500">{progressStage}</p>
								{/if}
							{:else}
								<div class="h-2.5 overflow-hidden rounded-full bg-primary/15">
									<div class="h-full w-1/3 animate-indeterminate rounded-full bg-primary/60"></div>
								</div>
							{/if}
						</div>
					{/if}

					<!-- View detail link -->
					<a href="/jobs/{job.job_id}" class="inline-block text-xs text-primary hover:underline">View full details</a>
				</div>
			</div>
		</div>
	{/if}
</div>
