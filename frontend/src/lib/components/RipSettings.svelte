<script lang="ts">
	import type { Job, JobConfigUpdate } from '$lib/types/arm';
	import { updateJobConfig } from '$lib/api/jobs';

	interface Props {
		job: Job;
		config: Record<string, string | null>;
		isMusic?: boolean;
		multiTitle?: boolean;
		onsaved?: () => void;
	}

	let { job, config, isMusic = false, multiTitle = false, onsaved }: Props = $props();

	let ripmethod = $state(String(config.RIPMETHOD ?? 'mkv').toLowerCase());
	let disctype = $state(String(config.DISCTYPE ?? job.disctype ?? 'dvd').toLowerCase());
	let mainfeature = $state(
		config.MAINFEATURE === '1' || String(config.MAINFEATURE ?? '').toLowerCase() === 'true'
	);
	let minlength = $state(Number(config.MINLENGTH) || 120);
	let maxlength = $state(Number(config.MAXLENGTH) || 99999);
	let audioFormat = $state(String(config.AUDIO_FORMAT ?? 'flac').toLowerCase());

	// Naming patterns for current media type
	let namingPatterns = $derived.by(() => {
		const vtype = job.video_type?.toLowerCase();
		if (isMusic || disctype === 'music') {
			return {
				label: 'Music',
				title: config.MUSIC_TITLE_PATTERN ?? '{artist} - {album}',
				folder: config.MUSIC_FOLDER_PATTERN ?? '{artist}/{album} ({year})',
				titleKey: 'MUSIC_TITLE_PATTERN',
				folderKey: 'MUSIC_FOLDER_PATTERN',
			};
		}
		if (vtype === 'series') {
			return {
				label: 'TV',
				title: config.TV_TITLE_PATTERN ?? '{title} S{season}E{episode}',
				folder: config.TV_FOLDER_PATTERN ?? '{title}/Season {season}',
				titleKey: 'TV_TITLE_PATTERN',
				folderKey: 'TV_FOLDER_PATTERN',
			};
		}
		return {
			label: 'Movie',
			title: config.MOVIE_TITLE_PATTERN ?? '{title} ({year})',
			folder: config.MOVIE_FOLDER_PATTERN ?? '{title} ({year})',
			titleKey: 'MOVIE_TITLE_PATTERN',
			folderKey: 'MOVIE_FOLDER_PATTERN',
		};
	});

	let saving = $state(false);
	let feedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);

	async function handleSave() {
		saving = true;
		feedback = null;
		try {
			const data: Partial<JobConfigUpdate> = {
				RIPMETHOD: ripmethod as 'mkv' | 'backup',
				DISCTYPE: disctype as 'dvd' | 'bluray' | 'bluray4k' | 'music' | 'data',
				MAINFEATURE: mainfeature,
				MINLENGTH: minlength,
				MAXLENGTH: maxlength,
				AUDIO_FORMAT: audioFormat
			};
			await updateJobConfig(job.job_id, data);
			feedback = { type: 'success', message: 'Settings saved' };
			onsaved?.();
		} catch (e) {
			feedback = { type: 'error', message: e instanceof Error ? e.message : 'Save failed' };
		} finally {
			saving = false;
		}
	}

	const inputClass =
		'rounded-lg border border-primary/25 bg-primary/5 px-3 py-1.5 text-sm text-gray-900 focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white';
	const labelClass = 'text-sm font-medium text-gray-700 dark:text-gray-300';
	const btnBase =
		'rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-50 transition-colors';
</script>

<div class="space-y-4">
	<div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
		{#if !isMusic}
			<label class="space-y-1">
				<span class={labelClass}>Rip Method</span>
				<select bind:value={ripmethod} class="{inputClass} w-full">
					<option value="mkv">MKV</option>
					<option value="backup">Backup (ISO)</option>
				</select>
			</label>
		{/if}

		<label class="space-y-1">
			<span class={labelClass}>Disc Type</span>
			<select bind:value={disctype} class="{inputClass} w-full">
				<option value="dvd">DVD</option>
				<option value="bluray">Blu-ray</option>
				<option value="bluray4k">4K UHD</option>
				<option value="music">Music</option>
				<option value="data">Data</option>
			</select>
		</label>

		{#if !isMusic && !multiTitle}
			<div class="space-y-1">
				<label class="flex items-center gap-2">
					<input
						type="checkbox"
						bind:checked={mainfeature}
						class="h-4 w-4 rounded-sm border-primary/25 text-primary focus:ring-primary dark:border-primary/30 dark:bg-primary/10"
					/>
					<span class={labelClass}>Main Feature Only</span>
				</label>
				<p class="text-xs text-gray-500 dark:text-gray-400">Auto-enable only the best track; when off, all tracks are enabled</p>
			</div>
		{/if}

		{#if !isMusic}
			<label class="space-y-1">
				<span class={labelClass}>Min Length (s)</span>
				<input type="number" bind:value={minlength} min="0" class="{inputClass} w-full" />
			</label>

			<label class="space-y-1">
				<span class={labelClass}>Max Length (s)</span>
				<input type="number" bind:value={maxlength} min="0" class="{inputClass} w-full" />
			</label>
		{/if}
	</div>

	{#if isMusic}
		<div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
			<label class="space-y-1">
				<span class={labelClass}>Audio Format</span>
				<select bind:value={audioFormat} class="{inputClass} w-full">
					<optgroup label="Common">
						<option value="flac">FLAC</option>
						<option value="mp3">MP3</option>
						<option value="vorbis">Ogg Vorbis</option>
						<option value="opus">Opus</option>
						<option value="m4a">AAC (M4A)</option>
						<option value="wav">WAV</option>
					</optgroup>
					<optgroup label="Other">
						<option value="wv">WavPack</option>
						<option value="ape">Monkey's Audio</option>
						<option value="mpc">Musepack</option>
						<option value="spx">Speex</option>
						<option value="mp2">MP2</option>
						<option value="tta">TTA</option>
						<option value="aiff">AIFF</option>
						<option value="mka">Matroska Audio</option>
					</optgroup>
				</select>
			</label>
		</div>
	{/if}

	<!-- Naming patterns (read-only, from global settings) -->
	<div class="rounded-lg border border-primary/15 bg-primary/[0.03] p-3 dark:border-primary/20 dark:bg-primary/5">
		<div class="mb-2 flex items-center justify-between">
			<span class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
				{namingPatterns.label} Naming
			</span>
			<a
				href="/settings"
				class="text-[10px] font-medium text-primary hover:underline dark:text-primary"
			>
				Edit in Settings
			</a>
		</div>
		<div class="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
			<div>
				<span class="text-[10px] font-medium text-gray-400 dark:text-gray-500">Title</span>
				<p class="font-mono text-xs text-gray-700 dark:text-gray-300">{namingPatterns.title}</p>
			</div>
			<div>
				<span class="text-[10px] font-medium text-gray-400 dark:text-gray-500">Folder</span>
				<p class="font-mono text-xs text-gray-700 dark:text-gray-300">{namingPatterns.folder}</p>
			</div>
		</div>
	</div>

	<div class="flex items-center gap-2">
		<button
			onclick={handleSave}
			disabled={saving}
			class="{btnBase} bg-green-600 text-white hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600"
		>
			{saving ? 'Saving...' : 'Save Settings'}
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
