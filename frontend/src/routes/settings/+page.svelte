<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchSettings, saveArmConfig, saveTranscoderConfig, testMetadataKey, testTranscoderConnection, testTranscoderWebhook, fetchSystemInfo, fetchAbcdeConfig, saveAbcdeConfig } from '$lib/api/settings';
	import type { ConnectionTestResult, WebhookTestResult, SystemInfoData } from '$lib/api/settings';
	import type { SettingsData, Drive } from '$lib/types/arm';
	import { theme, toggleTheme } from '$lib/stores/theme';
	import { colorScheme, COLOR_SCHEMES, schemeLocksMode } from '$lib/stores/colorScheme';
	import { createPollingStore } from '$lib/stores/polling';
	import { fetchDrives, fetchDriveDiagnostic } from '$lib/api/drives';
	import type { DiagnosticResult } from '$lib/api/drives';
	import DriveCard from '$lib/components/DriveCard.svelte';

	let settings = $state<SettingsData | null>(null);
	let error = $state<string | null>(null);

	// --- Transcoder form state ---
	let tcForm = $state<Record<string, unknown>>({});
	let tcOriginal = $state<Record<string, unknown>>({});
	let tcSaving = $state(false);
	let tcFeedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);

	// --- ARM form state ---
	let armForm = $state<Record<string, string | null>>({});
	let armOriginal = $state<Record<string, string | null>>({});
	let armSaving = $state(false);
	let armFeedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);
	let armRevealedKeys = $state<Set<string>>(new Set());
	let armCollapsed = $state<Record<string, boolean>>({});

	// --- Tab state ---
	const validTabs = ['ripping', 'music', 'transcoding', 'notifications', 'appearance', 'drives', 'system'] as const;
	type Tab = typeof validTabs[number];

	function parseHash(): { tab: Tab; panel: string | null } {
		if (typeof window === 'undefined') return { tab: 'ripping', panel: null };
		const hash = window.location.hash.replace('#', '');
		const [tabPart, ...panelParts] = hash.split('/');
		const tab = validTabs.includes(tabPart as Tab) ? (tabPart as Tab) : 'ripping';
		const panel = panelParts.length > 0 ? decodeURIComponent(panelParts.join('/')) : null;
		return { tab, panel };
	}

	let activeTab = $state<Tab>(parseHash().tab);
	let pendingPanel = $state<string | null>(parseHash().panel);

	// --- Drives polling store ---
	const drives = createPollingStore(fetchDrives, [] as Drive[], 10000);
	const driveError = drives.error;

	// --- Drive diagnostics ---
	let diagRunning = $state(false);
	let diagResult = $state<DiagnosticResult | null>(null);
	let diagError = $state<string | null>(null);

	async function runDiagnostic() {
		if (diagRunning) return;
		diagRunning = true;
		diagError = null;
		try {
			diagResult = await fetchDriveDiagnostic();
		} catch (e) {
			diagError = e instanceof Error ? e.message : 'Diagnostic failed';
			diagResult = null;
		} finally {
			diagRunning = false;
		}
	}

	// --- Search/filter ---
	let armSearch = $state('');

	// --- Metadata test ---
	let metadataTestResult = $state<{ success: boolean; message: string } | null>(null);
	let metadataTesting = $state(false);

	// --- Transcoder connection test ---
	let connTesting = $state(false);
	let connResult = $state<ConnectionTestResult | null>(null);

	// --- Transcoder webhook test ---
	let webhookTesting = $state(false);
	let webhookResult = $state<WebhookTestResult | null>(null);
	let webhookSecret = $state('');

	// --- System Info state ---
	let systemInfo = $state<SystemInfoData | null>(null);
	let systemInfoLoading = $state(false);
	let systemInfoLoaded = $state(false);

	// --- abcde.conf editor state ---
	let abcdeContent = $state('');
	let abcdeOriginal = $state('');
	let abcdePath = $state('');
	let abcdeExists = $state(false);
	let abcdeLoading = $state(false);
	let abcdeSaving = $state(false);
	let abcdeLoaded = $state(false);
	let abcdeFeedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);
	let abcdeDirty = $derived(abcdeContent !== abcdeOriginal);
	let abcdeCollapsed = $state(false);

	async function loadAbcdeConfig() {
		if (abcdeLoaded) return;
		abcdeLoading = true;
		try {
			const data = await fetchAbcdeConfig();
			abcdeContent = data.content;
			abcdeOriginal = data.content;
			abcdePath = data.path;
			abcdeExists = data.exists;
			abcdeLoaded = true;
		} catch {
			// silently fail, will show empty state
		} finally {
			abcdeLoading = false;
		}
	}

	async function handleAbcdeSave() {
		abcdeSaving = true;
		abcdeFeedback = null;
		try {
			await saveAbcdeConfig(abcdeContent);
			abcdeOriginal = abcdeContent;
			abcdeExists = true;
			abcdeFeedback = { type: 'success', message: 'abcde.conf saved' };
		} catch (e) {
			abcdeFeedback = { type: 'error', message: e instanceof Error ? e.message : 'Failed to save' };
		} finally {
			abcdeSaving = false;
			clearFeedback(() => (abcdeFeedback = null));
		}
	}

	function handleAbcdeDiscard() {
		abcdeContent = abcdeOriginal;
	}

	// --- abcde.conf search ---
	let abcdeSearch = $state('');
	let abcdeSearchIndex = $state(0);
	let abcdeTextarea = $state<HTMLTextAreaElement | null>(null);

	let abcdeMatches = $derived.by<number[]>(() => {
		if (!abcdeSearch) return [];
		const q = abcdeSearch.toLowerCase();
		const text = abcdeContent.toLowerCase();
		const positions: number[] = [];
		let idx = 0;
		while ((idx = text.indexOf(q, idx)) !== -1) {
			positions.push(idx);
			idx += 1;
		}
		return positions;
	});

	function abcdeSearchNav(delta: number) {
		if (abcdeMatches.length === 0) return;
		abcdeSearchIndex = (abcdeSearchIndex + delta + abcdeMatches.length) % abcdeMatches.length;
		const pos = abcdeMatches[abcdeSearchIndex];
		if (abcdeTextarea) {
			abcdeTextarea.focus();
			abcdeTextarea.setSelectionRange(pos, pos + abcdeSearch.length);
			// Scroll selection into view by briefly blurring/focusing
			const linesBefore = abcdeContent.substring(0, pos).split('\n').length;
			const lineHeight = abcdeTextarea.scrollHeight / abcdeContent.split('\n').length;
			abcdeTextarea.scrollTop = Math.max(0, (linesBefore - 3) * lineHeight);
		}
	}

	async function loadSystemInfo() {
		if (systemInfoLoaded) return;
		systemInfoLoading = true;
		try {
			systemInfo = await fetchSystemInfo();
			systemInfoLoaded = true;
		} catch (e) {
			// silently fail, will show empty state
		} finally {
			systemInfoLoading = false;
		}
	}

	function setTab(tab: Tab) {
		activeTab = tab;
		pendingPanel = null;
		window.location.hash = tab;
		if (tab === 'music') loadAbcdeConfig();
		if (tab === 'system') loadSystemInfo();
	}

	function scrollToPanel(label: string) {
		// Expand the panel first
		armCollapsed[label] = false;
		// Scroll to it after DOM update
		requestAnimationFrame(() => {
			const el = document.getElementById(`panel-${label.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`);
			el?.scrollIntoView({ behavior: 'smooth', block: 'start' });
		});
	}

	onMount(() => {
		drives.start();
		loadSettings().then(() => {
			if (pendingPanel) {
				// Find the panel label case-insensitively
				const groups = TAB_ARM_GROUPS[activeTab] ?? [];
				const match = groups.find((g) => g.label.toLowerCase().replace(/[^a-z0-9]+/g, '-') === pendingPanel!.toLowerCase().replace(/[^a-z0-9]+/g, '-'));
				if (match) scrollToPanel(match.label);
				pendingPanel = null;
			}
		});
		// Handle initial hash tab (trigger side effects)
		if (activeTab === 'music') loadAbcdeConfig();
		if (activeTab === 'system') loadSystemInfo();
		function onHashChange() {
			const { tab, panel } = parseHash();
			activeTab = tab;
			if (panel) {
				const groups = TAB_ARM_GROUPS[tab] ?? [];
				const match = groups.find((g) => g.label.toLowerCase().replace(/[^a-z0-9]+/g, '-') === panel.toLowerCase().replace(/[^a-z0-9]+/g, '-'));
				if (match) scrollToPanel(match.label);
			}
		}
		window.addEventListener('hashchange', onHashChange);
		return () => { drives.stop(); window.removeEventListener('hashchange', onHashChange); };
	});

	async function loadSettings() {
		try {
			settings = await fetchSettings();
			if (settings?.transcoder_config?.config) {
				tcForm = { ...settings.transcoder_config.config };
				tcOriginal = { ...settings.transcoder_config.config };
			}
			if (settings?.arm_config) {
				armForm = { ...settings.arm_config };
				armOriginal = { ...settings.arm_config };
			}
			// Collapse Emby Integration by default
			armCollapsed['Emby Integration'] = true;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load settings';
		}
	}

	function clearFeedback(setter: (v: null) => void) {
		setTimeout(() => setter(null), 4000);
	}

	// --- Transcoder dirty check ---
	let tcDirty = $derived(JSON.stringify(tcForm) !== JSON.stringify(tcOriginal));

	async function handleTcSave() {
		tcSaving = true;
		tcFeedback = null;
		const changed: Record<string, unknown> = {};
		for (const [key, val] of Object.entries(tcForm)) {
			if (JSON.stringify(val) !== JSON.stringify(tcOriginal[key])) {
				changed[key] = val;
			}
		}
		try {
			const result = await saveTranscoderConfig(changed);
			if (result.applied) {
				Object.assign(tcForm, result.applied);
				tcOriginal = { ...tcForm };
			}
			tcFeedback = { type: 'success', message: 'Transcoder settings saved' };
		} catch (e) {
			tcFeedback = { type: 'error', message: e instanceof Error ? e.message : 'Failed to save' };
		} finally {
			tcSaving = false;
			clearFeedback(() => (tcFeedback = null));
		}
	}

	// --- ARM dirty check ---
	let armDirty = $derived(JSON.stringify(armForm) !== JSON.stringify(armOriginal));

	async function handleArmSave() {
		armSaving = true;
		armFeedback = null;
		try {
			const result = await saveArmConfig(armForm);
			if (result.warning) {
				armFeedback = { type: 'success', message: `Saved (${result.warning})` };
			} else {
				armFeedback = { type: 'success', message: 'ARM settings saved' };
			}
			armOriginal = { ...armForm };
		} catch (e) {
			armFeedback = { type: 'error', message: e instanceof Error ? e.message : 'Failed to save' };
		} finally {
			armSaving = false;
			clearFeedback(() => (armFeedback = null));
		}
	}

	// Any tab dirty — sticky bar persists across tab switches
	let anyDirty = $derived(armDirty || tcDirty);
	let anySaving = $derived(armSaving || tcSaving);
	let anyFeedback = $derived(armFeedback ?? tcFeedback);

	function handleSaveAll() {
		if (armDirty) handleArmSave();
		if (tcDirty) handleTcSave();
	}

	function handleDiscardAll() {
		if (armDirty) armForm = { ...armOriginal };
		if (tcDirty) tcForm = { ...tcOriginal };
	}

	let dirtyTabLabel = $derived(
		armDirty && tcDirty ? 'ARM & Transcoder' : armDirty ? 'ARM settings' : 'Transcoder'
	);

	// Transcoder base paths (read-only, for display in directories panel)
	let tcPaths = $derived(settings?.transcoder_config?.paths);

	// --- GPU support labels (transcoder only) ---
	const GPU_LABELS: Record<string, string> = {
		ffmpeg_nvenc_h265: 'FFmpeg NVENC H.265',
		ffmpeg_nvenc_h264: 'FFmpeg NVENC H.264',
		ffmpeg_vaapi_h265: 'FFmpeg VAAPI H.265',
		ffmpeg_vaapi_h264: 'FFmpeg VAAPI H.264',
		ffmpeg_amf_h265: 'FFmpeg AMF H.265',
		ffmpeg_amf_h264: 'FFmpeg AMF H.264',
		ffmpeg_qsv_h265: 'FFmpeg QSV H.265',
		ffmpeg_qsv_h264: 'FFmpeg QSV H.264',
		vaapi_device: 'VAAPI Render Device',
	};

	const HW_GROUPS = [
		{ label: 'Nvidia NVENC', keys: ['ffmpeg_nvenc_h265', 'ffmpeg_nvenc_h264'] },
		{ label: 'Intel QuickSync', keys: ['ffmpeg_qsv_h265', 'ffmpeg_qsv_h264'] },
		{ label: 'AMD VCN', keys: ['ffmpeg_amf_h265', 'ffmpeg_amf_h264'] },
		{ label: 'VAAPI (AMD/Intel)', keys: ['ffmpeg_vaapi_h265', 'ffmpeg_vaapi_h264', 'vaapi_device'] },
	];

	function hasAny(gpu: Record<string, boolean>, keys: string[]): boolean {
		return keys.some((k) => gpu[k]);
	}

	// --- Transcoder field labels ---
	const TC_LABELS: Record<string, string> = {
		video_encoder: 'Video Encoder',
		video_quality: 'Video Quality (CRF)',
		audio_encoder: 'Audio Encoder',
		subtitle_mode: 'Subtitle Mode',
		handbrake_preset: 'HandBrake Preset (Default)',
		handbrake_preset_4k: 'HandBrake Preset (4K)',
		handbrake_preset_dvd: 'HandBrake Preset (DVD)',
		handbrake_preset_file: 'Custom Preset File',
		delete_source: 'Delete Source After Transcode',
		output_extension: 'Output Extension',
		movies_subdir: 'Movies Subdirectory',
		tv_subdir: 'TV Shows Subdirectory',
		audio_subdir: 'Audio Subdirectory',
		max_concurrent: 'Max Concurrent Transcodes',
		stabilize_seconds: 'Stabilize Wait (seconds)',
		minimum_free_space_gb: 'Min Free Disk Space (GB)',
		max_retry_count: 'Max Retry Attempts',
		log_level: 'Log Level',
		log_level_libraries: 'Log Level (Libraries)',
	};

	// Transcoder boolean fields rendered as toggle switches
	const TC_BOOL_KEYS = new Set(['delete_source']);

	// Preset keys rendered in their own 3-column row
	const TC_PRESET_KEYS = ['handbrake_preset', 'handbrake_preset_4k', 'handbrake_preset_dvd'];
	const TC_PRESET_SET = new Set([
		...TC_PRESET_KEYS,
		'handbrake_preset_file',
		'video_encoder',
		// Audio panel keys
		'audio_encoder',
		'subtitle_mode',
		// Directory panel keys
		'movies_subdir',
		'tv_subdir',
		'audio_subdir',
		'output_extension',
		'delete_source',
	]);

	// Video encoder options — canonical encoders only (no aliases), with labels
	const VIDEO_ENCODER_OPTIONS: { value: string; label: string }[] = [
		{ value: 'nvenc_h265', label: 'NVENC H.265 (Nvidia)' },
		{ value: 'nvenc_h264', label: 'NVENC H.264 (Nvidia)' },
		{ value: 'qsv_h265', label: 'QSV H.265 (Intel)' },
		{ value: 'qsv_h264', label: 'QSV H.264 (Intel)' },
		{ value: 'vaapi_h265', label: 'VAAPI H.265 (AMD/Intel)' },
		{ value: 'vaapi_h264', label: 'VAAPI H.264 (AMD/Intel)' },
		{ value: 'amf_h265', label: 'AMF H.265 (AMD)' },
		{ value: 'amf_h264', label: 'AMF H.264 (AMD)' },
		{ value: 'x265', label: 'Software H.265' },
		{ value: 'x264', label: 'Software H.264' },
	];

	// Transcoder number fields: key → [min, max, step?]
	const TC_NUMBER_FIELDS: Record<string, [number, number, number?]> = {
		video_quality: [0, 51],
		max_concurrent: [1, 10],
		stabilize_seconds: [10, 600],
		minimum_free_space_gb: [1, 500, 0.5],
		max_retry_count: [0, 10],
	};

	// Help text for transcoder fields
	const TC_HELP: Record<string, string> = {
		video_encoder: 'Auto-detected from GPU at startup. NVENC (Nvidia), QSV (Intel), VCN/VAAPI (AMD), or x265 (software).',
		handbrake_preset: 'Default preset for sources 720p–1080p. Auto-detected from GPU at startup.',
		handbrake_preset_4k: 'Used for 4K UHD sources (>1080p). Auto-detected from GPU at startup.',
		handbrake_preset_dvd: 'Used for DVD/low-res sources (<720p). Falls back to the default preset if empty.',
		handbrake_preset_file:
			'Imports custom presets from a JSON file. When set, those preset names become available alongside built-in presets.',
		log_level_libraries:
			'Log level for third-party libraries (aiosqlite, httpcore, httpx, uvicorn). Defaults to WARNING to reduce noise.',
	};

	// Preset options: custom presets from selected file first, then built-in.
	// Always includes custom presets from valid_handbrake_presets so current values are selectable.
	let presetOptions = $derived.by<string[]>(() => {
		const builtin = settings?.arm_handbrake_presets ?? [];
		const tcCustom = settings?.transcoder_config?.valid_handbrake_presets ?? [];
		const byFile = settings?.transcoder_config?.presets_by_file ?? {};
		const selectedFile = tcForm.handbrake_preset_file as string;

		// When a file is selected, show its presets first
		const filePresets = selectedFile ? (byFile[selectedFile] ?? []) : [];
		const seen = new Set<string>(filePresets);

		// Then custom presets from transcoder (may overlap)
		const extraCustom = tcCustom.filter((n: string) => !seen.has(n));
		extraCustom.forEach((n: string) => seen.add(n));

		// Then built-in presets
		const extraBuiltin = builtin.filter((n: string) => !seen.has(n));

		return [...filePresets, ...extraCustom, ...extraBuiltin];
	});

	// When the preset file changes, auto-fill preset names from it
	function handlePresetFileChange(newFile: string) {
		tcForm.handbrake_preset_file = newFile;
		if (!newFile) return;

		const byFile = settings?.transcoder_config?.presets_by_file ?? {};
		const filePresets = byFile[newFile] ?? [];
		if (filePresets.length === 0) return;

		// Auto-fill: pick presets by resolution hint
		const is4k = (n: string) => /4k|2160/i.test(n);
		const isDvd = (n: string) => /dvd|480|576|720p/i.test(n);
		const preset4k = filePresets.find(is4k);
		const presetDvd = filePresets.find(isDvd);
		const presetStd = filePresets.find((n: string) => !is4k(n) && !isDvd(n)) ?? filePresets[0];

		if (presetStd) tcForm.handbrake_preset = presetStd;
		if (preset4k) tcForm.handbrake_preset_4k = preset4k;
		if (presetDvd) tcForm.handbrake_preset_dvd = presetDvd;
	}

	// Returns the valid options array for select-type transcoder fields, or null.
	// Always includes the current value so the select never shows blank.
	function tcSelectOptions(key: string): string[] | null {
		if (!settings?.transcoder_config) return null;
		const tc = settings.transcoder_config;
		const presetFiles = tc.valid_preset_files;
		const presets = presetOptions;
		const map: Record<string, string[] | undefined> = {
			audio_encoder: tc.valid_audio_encoders,
			subtitle_mode: tc.valid_subtitle_modes,
			log_level: tc.valid_log_levels,
			log_level_libraries: tc.valid_log_levels,
			handbrake_preset: presets.length ? ['', ...presets] : undefined,
			handbrake_preset_4k: presets.length ? ['', ...presets] : undefined,
			handbrake_preset_dvd: presets.length ? ['', ...presets] : undefined,
			handbrake_preset_file: presetFiles?.length ? ['', ...presetFiles] : undefined,
		};
		const opts = map[key] ?? null;
		if (!opts) return null;

		// Ensure the current value is in the options list
		const current = tcForm[key];
		if (current && typeof current === 'string' && !opts.includes(current)) {
			return [current, ...opts];
		}
		return opts;
	}

	// --- ARM human-readable labels ---
	const ARM_LABELS: Record<string, { label: string; description: string }> = {
		// Video Ripping
		VIDEOTYPE: { label: 'Video Type', description: 'auto, series, or movie — how to identify inserted discs' },
		RIPMETHOD: { label: 'Rip Method', description: 'mkv (MakeMKV), backup (full disc), or backup_dvd' },
		PREVENT_99: { label: 'Track 99 Protection', description: 'Eject discs with DRM fake-title schemes instead of risking a hang' },
		ARM_CHECK_UDF: { label: 'Check UDF Filesystem', description: 'Distinguish UDF video discs from data discs' },
		GET_VIDEO_TITLE: { label: 'Lookup Video Title', description: 'Query metadata services for the movie/series title' },
		MINLENGTH: { label: 'Minimum Track Length', description: 'Minimum title length in seconds to rip' },
		MAXLENGTH: { label: 'Maximum Track Length', description: 'Maximum title length in seconds to rip' },
		MAINFEATURE: { label: 'Main Feature Only', description: 'Rip only the longest title on the disc' },
		MANUAL_WAIT: { label: 'Wait for Manual ID', description: 'Pause for user to manually identify the disc' },
		MANUAL_WAIT_TIME: { label: 'Manual Wait Time', description: 'Seconds to wait for manual identification' },
		ALLOW_DUPLICATES: { label: 'Allow Duplicates', description: 'Allow ripping a disc that has already been ripped' },
		MKV_ARGS: { label: 'MakeMKV Arguments', description: 'Extra command-line arguments passed to MakeMKV' },
		MAKEMKV_PERMA_KEY: { label: 'MakeMKV License Key', description: 'Permanent key from <a href="https://www.makemkv.com/buy/" target="_blank" rel="noopener" class="underline text-primary hover:text-primary-hover">makemkv.com/buy</a> — free beta keys are also available on the <a href="https://forum.makemkv.com/forum/viewtopic.php?t=1053" target="_blank" rel="noopener" class="underline text-primary hover:text-primary-hover">MakeMKV forum</a>' },
		DATA_RIP_PARAMETERS: { label: 'Data Rip Parameters', description: 'Extra parameters for data disc ripping' },
		MAX_CONCURRENT_MAKEMKVINFO: { label: 'Max Concurrent Disc Scans', description: 'Limit parallel makemkvinfo processes (0 = unlimited)' },
		AUTO_EJECT: { label: 'Auto-Eject After Rip', description: 'Eject the disc when ripping completes' },
		RIP_POSTER: { label: 'Download Poster', description: 'Save movie poster artwork during ripping' },
		MAKEMKV_COMMUNITY_KEYDB: { label: 'Community Key Database', description: 'Download community keydb.cfg at container startup' },
		ARM_CHILDREN: { label: 'ARM Child Servers', description: 'Comma-delimited list of child ARM server URLs' },
		DELRAWFILES: { label: 'Delete Raw Files', description: 'Remove raw MakeMKV output after processing' },
		DRIVE_READY_TIMEOUT: { label: 'Drive Ready Timeout', description: 'Seconds to wait for the drive to become ready after disc insertion' },
		// TV Series
		USE_DISC_LABEL_FOR_TV: { label: 'Use Disc Label for TV', description: 'Parse disc label for season/episode info on TV series discs' },
		GROUP_TV_DISCS_UNDER_SERIES: { label: 'Group TV Discs Under Series', description: 'Group multi-disc TV sets under a single series folder' },
		// Music Ripping
		GET_AUDIO_TITLE: { label: 'Audio Metadata Source', description: 'none, musicbrainz, or freecddb for CD track info' },
		AUDIO_FORMAT: { label: 'Audio Format', description: 'Output format for music CD ripping (passed to abcde -o)' },
		ABCDE_CONFIG_FILE: { label: 'abcde Config File', description: 'Path to the abcde configuration file for CD ripping' },
		RIP_SPEED_PROFILE: { label: 'Rip Speed Profile', description: '"safe" = full paranoia (best for scratched discs), "fast" = less paranoia (~2-4x faster), "fastest" = no error correction (pristine discs only)' },
		MUSIC_MULTI_DISC_SUBFOLDERS: { label: 'Multi-Disc Subfolders', description: 'Create per-disc subfolders for multi-CD sets (e.g. Artist/Album/Disc 1/)' },
		MUSIC_DISC_FOLDER_PATTERN: { label: 'Disc Folder Pattern', description: 'Folder name for each disc in a multi-disc set. {num} = disc number. Examples: "Disc {num}", "CD {num}"' },
		// Metadata
		METADATA_PROVIDER: { label: 'Metadata Provider', description: 'omdb or tmdb for movie/TV lookups' },
		OMDB_API_KEY: { label: 'OMDb API Key', description: 'API key for the Open Movie Database' },
		TMDB_API_KEY: { label: 'TMDb API Key', description: 'API key for The Movie Database' },
		// General
		ARM_NAME: { label: 'Machine Name', description: 'Friendly name for this ARM instance, used in notifications' },
		DISABLE_LOGIN: { label: 'Disable Login', description: 'Skip authentication — leave all pages open' },
		DATE_FORMAT: { label: 'Date Format', description: 'strftime format string for timestamps' },
		ARM_API_KEY: { label: 'ARM API Key', description: 'API key for the ARM disc CRC lookup service' },
		// Web Server
		WEBSERVER_IP: { label: 'Web Server IP', description: 'IP address the ARM web UI binds to' },
		WEBSERVER_PORT: { label: 'Web Server Port', description: 'Port the ARM web UI listens on' },
		UI_BASE_URL: { label: 'UI Base URL', description: 'Base URL for the ARM web interface (for reverse proxies)' },
		// Paths & Storage
		RAW_PATH: { label: 'Raw Output Path', description: 'Directory where MakeMKV writes ripped files' },
		TRANSCODE_PATH: { label: 'Transcode Path', description: 'Staging directory for transcoding work' },
		COMPLETED_PATH: { label: 'Completed Path', description: 'Final destination for finished media files' },
		MUSIC_PATH: { label: 'Music Path', description: 'Output directory for music CD rips (used by abcde)' },
		EXTRAS_SUB: { label: 'Extras Subdirectory', description: 'Subfolder name for bonus features and extras' },
		INSTALLPATH: { label: 'Install Path', description: 'ARM installation directory' },
		LOGPATH: { label: 'Log Path', description: 'Directory for ARM log files' },
		LOGLEVEL: { label: 'Log Level', description: 'Logging verbosity: DEBUG, INFO, WARNING, ERROR, CRITICAL' },
		LOGLIFE: { label: 'Log Retention (days)', description: 'Number of days to keep log files' },
		DBFILE: { label: 'Database File', description: 'Path to the ARM SQLite database' },
		UMASK: { label: 'File Umask', description: 'Umask applied to files created by ARM' },
		SET_MEDIA_PERMISSIONS: { label: 'Set Media Permissions', description: 'Apply chmod to completed media files' },
		CHMOD_VALUE: { label: 'Chmod Value', description: 'Permission bits to apply (e.g. 777)' },
		SET_MEDIA_OWNER: { label: 'Set Media Owner', description: 'Apply chown to completed media files' },
		CHOWN_USER: { label: 'Owner User', description: 'User to own completed media files' },
		CHOWN_GROUP: { label: 'Owner Group', description: 'Group to own completed media files' },
		// Emby
		EMBY_REFRESH: { label: 'Emby Library Refresh', description: 'Trigger an Emby library scan after ripping' },
		EMBY_SERVER: { label: 'Emby Server', description: 'Emby server hostname or IP' },
		EMBY_PORT: { label: 'Emby Port', description: 'Emby server port' },
		EMBY_CLIENT: { label: 'Emby Client Name', description: 'Client identifier sent to Emby' },
		EMBY_DEVICE: { label: 'Emby Device Name', description: 'Device name sent to Emby' },
		EMBY_DEVICEID: { label: 'Emby Device ID', description: 'Unique device identifier for Emby' },
		EMBY_USERNAME: { label: 'Emby Username', description: 'Emby account username' },
		EMBY_USERID: { label: 'Emby User ID', description: 'Emby internal user ID' },
		EMBY_PASSWORD: { label: 'Emby Password', description: 'Emby account password' },
		EMBY_API_KEY: { label: 'Emby API Key', description: 'API key for Emby server access' },
		// Notifications
		NOTIFY_RIP: { label: 'Notify After Rip', description: 'Send a notification when ripping completes' },
		NOTIFY_TRANSCODE: { label: 'Notify After Transcode', description: 'Send a notification when transcoding completes' },
		NOTIFY_JOBID: { label: 'Include Job ID', description: 'Append the job ID to notification titles' },
		PB_KEY: { label: 'Pushbullet Key', description: 'API key for Pushbullet notifications' },
		IFTTT_KEY: { label: 'IFTTT Key', description: 'Webhook key for IFTTT notifications' },
		IFTTT_EVENT: { label: 'IFTTT Event', description: 'IFTTT webhook event name' },
		PO_USER_KEY: { label: 'Pushover User Key', description: 'User key for Pushover notifications' },
		PO_APP_KEY: { label: 'Pushover App Key', description: 'Application key for Pushover notifications' },
		BASH_SCRIPT: { label: 'Notification Script', description: 'Path to a custom bash script run on notifications' },
		JSON_URL: { label: 'Apprise JSON URL', description: 'Apprise webhook URL for notifications' },
		APPRISE: { label: 'Apprise Config', description: 'Apprise notification service configuration string' },
		// TVDB
		TVDB_API_KEY: { label: 'TVDB API Key', description: 'API key for TheTVDB v4 — get one free at thetvdb.com/dashboard' },
		TVDB_MATCH_TOLERANCE: { label: 'Match Tolerance (sec)', description: 'Max runtime difference in seconds for a track-to-episode match (default 300)' },
		TVDB_MAX_SEASON_SCAN: { label: 'Max Season Scan', description: 'How many seasons to scan when auto-detecting season (default 10)' },
		// Naming Patterns
		MOVIE_TITLE_PATTERN: { label: 'Movie Title Pattern', description: 'Pattern for movie display titles' },
		MOVIE_FOLDER_PATTERN: { label: 'Movie Folder Pattern', description: 'Pattern for movie folder names (use / for nested directories)' },
		TV_TITLE_PATTERN: { label: 'TV Title Pattern', description: 'Pattern for TV series display titles' },
		TV_FOLDER_PATTERN: { label: 'TV Folder Pattern', description: 'Pattern for TV series folder names (use / for nested directories)' },
		MUSIC_TITLE_PATTERN: { label: 'Music Title Pattern', description: 'Pattern for music display titles' },
		MUSIC_FOLDER_PATTERN: { label: 'Music Folder Pattern', description: 'Pattern for music folder names (use / for nested directories)' },
		// Transcoder Integration
		TRANSCODER_URL: { label: 'Transcoder Webhook URL', description: 'URL of the arm-transcoder webhook endpoint (leave empty to disable)' },
		TRANSCODER_WEBHOOK_SECRET: { label: 'Transcoder Webhook Secret', description: 'Must match WEBHOOK_SECRET in arm-transcoder .env' },
		LOCAL_RAW_PATH: { label: 'Local Raw Path', description: 'Local scratch storage where ARM rips to (for file move before notify)' },
		SHARED_RAW_PATH: { label: 'Shared Raw Path', description: 'Shared/NFS storage the transcoder reads from (for file move before notify)' },
	};

	let armInfoKeys = $state<Set<string>>(new Set());
	let endpointInfoKeys = $state<Set<string>>(new Set());

	function toggleInfo(key: string) {
		const next = new Set(armInfoKeys);
		if (next.has(key)) next.delete(key);
		else next.add(key);
		armInfoKeys = next;
	}

	function toggleEndpointInfo(name: string) {
		const next = new Set(endpointInfoKeys);
		if (next.has(name)) next.delete(name);
		else next.add(name);
		endpointInfoKeys = next;
	}

	// --- ARM config groups, organized by tab ---
	type ArmGroup = { label: string; subpanels: { label?: string; keys: string[] }[] };

	const TAB_ARM_GROUPS: Record<string, ArmGroup[]> = {
		ripping: [
			{ label: 'Disc Identification', subpanels: [
				{ keys: ['VIDEOTYPE', 'GET_VIDEO_TITLE', 'ARM_CHECK_UDF', 'MANUAL_WAIT', 'MANUAL_WAIT_TIME', 'DRIVE_READY_TIMEOUT', 'ARM_CHILDREN'] },
			]},
			{ label: 'Track Selection', subpanels: [
				{ keys: ['MINLENGTH', 'MAXLENGTH', 'MAINFEATURE', 'PREVENT_99', 'ALLOW_DUPLICATES'] },
			]},
			{ label: 'TV Series', subpanels: [
				{ keys: ['USE_DISC_LABEL_FOR_TV', 'GROUP_TV_DISCS_UNDER_SERIES'] },
			]},
			{ label: 'Rip Method', subpanels: [
				{ keys: ['RIPMETHOD', 'MKV_ARGS', 'DATA_RIP_PARAMETERS'] },
			]},
			{ label: 'MakeMKV', subpanels: [
				{ keys: ['MAKEMKV_PERMA_KEY', 'MAKEMKV_COMMUNITY_KEYDB', 'MAX_CONCURRENT_MAKEMKVINFO'] },
			]},
			{ label: 'Post-Rip', subpanels: [
				{ keys: ['AUTO_EJECT', 'DELRAWFILES', 'RIP_POSTER'] },
			]},
			{ label: 'Media Directories', subpanels: [
				{ keys: ['RAW_PATH', 'TRANSCODE_PATH', 'COMPLETED_PATH', 'MUSIC_PATH', 'EXTRAS_SUB'] },
			]},
			{ label: 'File Permissions', subpanels: [
				{ keys: ['UMASK', 'SET_MEDIA_PERMISSIONS', 'CHMOD_VALUE', 'SET_MEDIA_OWNER', 'CHOWN_USER', 'CHOWN_GROUP'] },
			]},
			{ label: 'Naming Patterns', subpanels: [
				{ label: 'Movie',  keys: ['MOVIE_TITLE_PATTERN', 'MOVIE_FOLDER_PATTERN'] },
				{ label: 'TV',     keys: ['TV_TITLE_PATTERN', 'TV_FOLDER_PATTERN'] },
			]},
			{ label: 'Metadata', subpanels: [
				{ keys: ['METADATA_PROVIDER', 'OMDB_API_KEY', 'TMDB_API_KEY', 'ARM_API_KEY'] },
			]},
			{ label: 'TVDB (TV Episode Matching)', subpanels: [
				{ keys: ['TVDB_API_KEY', 'TVDB_MATCH_TOLERANCE', 'TVDB_MAX_SEASON_SCAN'] },
			]},
		],
		music: [
			{ label: 'Metadata', subpanels: [
				{ keys: ['GET_AUDIO_TITLE'] },
			]},
			{ label: 'Rip Speed', subpanels: [
				{ keys: ['RIP_SPEED_PROFILE'] },
			]},
			{ label: 'Naming Patterns', subpanels: [
				{ keys: ['MUSIC_TITLE_PATTERN', 'MUSIC_FOLDER_PATTERN'] },
			]},
			{ label: 'Multi-Disc Sets', subpanels: [
				{ keys: ['MUSIC_MULTI_DISC_SUBFOLDERS', 'MUSIC_DISC_FOLDER_PATTERN'] },
			]},
		],
		notifications: [
			{ label: 'Triggers', subpanels: [
				{ keys: ['NOTIFY_RIP', 'NOTIFY_TRANSCODE', 'NOTIFY_JOBID'] },
			]},
			{ label: 'Transcoder', subpanels: [
				{ keys: ['TRANSCODER_URL', 'TRANSCODER_WEBHOOK_SECRET', 'LOCAL_RAW_PATH', 'SHARED_RAW_PATH'] },
			]},
			{ label: 'Apprise', subpanels: [
				{ keys: ['JSON_URL', 'APPRISE'] },
			]},
			{ label: 'Pushbullet', subpanels: [
				{ keys: ['PB_KEY'] },
			]},
			{ label: 'Pushover', subpanels: [
				{ keys: ['PO_USER_KEY', 'PO_APP_KEY'] },
			]},
			{ label: 'IFTTT', subpanels: [
				{ keys: ['IFTTT_KEY', 'IFTTT_EVENT'] },
			]},
			{ label: 'Custom Script', subpanels: [
				{ keys: ['BASH_SCRIPT'] },
			]},
			{ label: 'Emby Integration', subpanels: [
				{ label: 'Connection', keys: ['EMBY_REFRESH', 'EMBY_SERVER', 'EMBY_PORT'] },
				{ label: 'Authentication', keys: ['EMBY_USERNAME', 'EMBY_USERID', 'EMBY_PASSWORD', 'EMBY_API_KEY'] },
				{ label: 'Client Identity', keys: ['EMBY_CLIENT', 'EMBY_DEVICE', 'EMBY_DEVICEID'] },
			]},
		],
		system: [
			{ label: 'Identity', subpanels: [
				{ keys: ['ARM_NAME', 'DISABLE_LOGIN', 'DATE_FORMAT'] },
			]},
			{ label: 'Web Server', subpanels: [
				{ keys: ['WEBSERVER_IP', 'WEBSERVER_PORT', 'UI_BASE_URL'] },
			]},
			{ label: 'System Paths & Logging', subpanels: [
				{ keys: ['INSTALLPATH', 'LOGPATH', 'DBFILE', 'LOGLEVEL', 'LOGLIFE'] },
			]},
		],
	};

	// All ARM groups flattened (for unmapped key detection)
	// Include keys rendered in the abcde.conf panel so they don't appear as "Other"
	const ALL_ARM_GROUPS = [
		...Object.values(TAB_ARM_GROUPS).flat(),
		{ label: '_abcde', subpanels: [{ keys: ['AUDIO_FORMAT', 'ABCDE_CONFIG_FILE'] }] },
	];

	const HIDDEN_KEYS = new Set([
		'OMDB_API_KEY',
		'EMBY_USERID',
		'EMBY_PASSWORD',
		'EMBY_API_KEY',
		'PB_KEY',
		'IFTTT_KEY',
		'PO_KEY',
		'PO_USER_KEY',
		'PO_APP_KEY',
		'ARM_API_KEY',
		'TMDB_API_KEY',
		'TVDB_API_KEY',
		'TRANSCODER_WEBHOOK_SECRET',
	]);

	// Keys hidden based on metadata provider selection
	const METADATA_API_KEYS = new Set(['OMDB_API_KEY', 'TMDB_API_KEY']);

	function isMetadataKeyHidden(key: string): boolean {
		if (!METADATA_API_KEYS.has(key)) return false;
		const provider = (armForm['METADATA_PROVIDER'] ?? 'omdb').toString().toLowerCase();
		if (key === 'OMDB_API_KEY') return provider !== 'omdb';
		if (key === 'TMDB_API_KEY') return provider !== 'tmdb';
		return false;
	}

	function isMetadataApiKey(key: string): boolean {
		return METADATA_API_KEYS.has(key);
	}

	async function handleTestMetadata() {
		metadataTesting = true;
		metadataTestResult = null;
		try {
			metadataTestResult = await testMetadataKey();
		} catch {
			metadataTestResult = { success: false, message: 'Failed to reach test endpoint' };
		} finally {
			metadataTesting = false;
			clearFeedback(() => (metadataTestResult = null));
		}
	}

	async function handleTestConnection() {
		connTesting = true;
		connResult = null;
		try {
			connResult = await testTranscoderConnection();
		} catch {
			connResult = { reachable: false, auth_ok: false, auth_required: false, gpu_support: null, worker_running: false, queue_size: 0, error: 'Failed to reach test endpoint' };
		} finally {
			connTesting = false;
		}
	}

	async function handleTestWebhook() {
		webhookTesting = true;
		webhookResult = null;
		try {
			webhookResult = await testTranscoderWebhook(webhookSecret);
		} catch {
			webhookResult = { reachable: false, secret_ok: false, secret_required: false, error: 'Failed to reach test endpoint' };
		} finally {
			webhookTesting = false;
		}
	}

	const SELECT_OPTIONS: Record<string, string[]> = {
		VIDEOTYPE: ['auto', 'series', 'movie'],
		RIPMETHOD: ['mkv', 'backup', 'backup_dvd'],
		LOGLEVEL: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
		METADATA_PROVIDER: ['omdb', 'tmdb'],
		GET_AUDIO_TITLE: ['none', 'musicbrainz', 'freecddb'],
		AUDIO_FORMAT: ['flac', 'mp3', 'vorbis', 'opus', 'm4a', 'wav', 'mka', 'wv', 'ape', 'mpc', 'spx', 'mp2', 'tta', 'aiff'],
	};

	// --- Search/filter logic ---
	function matchesSearch(key: string): boolean {
		if (!armSearch.trim()) return true;
		const q = armSearch.toLowerCase();
		const label = ARM_LABELS[key]?.label ?? key;
		const desc = ARM_LABELS[key]?.description ?? '';
		return (
			key.toLowerCase().includes(q) ||
			label.toLowerCase().includes(q) ||
			desc.toLowerCase().includes(q)
		);
	}

	function getArmGroups(config: Record<string, string | null>, tabGroups: ArmGroup[], includeUnmapped = false) {
		const allKeys = new Set(Object.keys(config));
		const mapped = new Set<string>();
		const groups: ArmGroup[] = [];

		for (const group of tabGroups) {
			const subpanels: { label?: string; keys: string[] }[] = [];
			for (const sp of group.subpanels) {
				const present = sp.keys.filter((k) => allKeys.has(k) && matchesSearch(k));
				sp.keys.filter((k) => allKeys.has(k)).forEach((k) => mapped.add(k));
				if (present.length > 0) {
					subpanels.push({ label: sp.label, keys: present });
				}
			}
			if (subpanels.length > 0) {
				groups.push({ label: group.label, subpanels });
			}
		}

		if (includeUnmapped) {
			// Track all keys mapped across ALL tabs (not just this one)
			const allMapped = new Set<string>();
			for (const g of ALL_ARM_GROUPS) {
				for (const sp of g.subpanels) {
					sp.keys.forEach((k) => allMapped.add(k));
				}
			}
			const unmapped = [...allKeys].filter((k) => !allMapped.has(k) && matchesSearch(k));
			if (unmapped.length > 0) {
				groups.push({ label: 'Other', subpanels: [{ keys: unmapped }] });
			}
		}

		return groups;
	}

	function isBoolStr(v: string | null): boolean {
		if (!v) return false;
		return v.toLowerCase() === 'true' || v.toLowerCase() === 'false';
	}

	function isIntStr(v: string | null): boolean {
		if (v === null || v === '') return false;
		return /^\d+$/.test(v);
	}

	function toggleBool(key: string) {
		const cur = (armForm[key] ?? 'false').toString().toLowerCase();
		armForm[key] = cur === 'true' ? 'false' : 'true';
	}

	function toggleCollapse(label: string) {
		armCollapsed[label] = !armCollapsed[label];
	}

	function toggleReveal(key: string) {
		const next = new Set(armRevealedKeys);
		if (next.has(key)) next.delete(key);
		else next.add(key);
		armRevealedKeys = next;
	}

	function getComment(key: string): string {
		if (!settings?.arm_metadata) return '';
		const raw = settings.arm_metadata[key];
		if (!raw || typeof raw !== 'string') return '';
		// Strip leading # characters and trim
		return raw.replace(/^#\s*/gm, '').trim();
	}

	// --- Dirty field check ---
	function isFieldDirty(key: string): boolean {
		return JSON.stringify(armForm[key]) !== JSON.stringify(armOriginal[key]);
	}

	function isTcFieldDirty(key: string): boolean {
		return JSON.stringify(tcForm[key]) !== JSON.stringify(tcOriginal[key]);
	}

	function formatBytes(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
		if (bytes < 1073741824) return `${(bytes / 1048576).toFixed(1)} MB`;
		return `${(bytes / 1073741824).toFixed(1)} GB`;
	}

	// Input class shared across all ARM fields
	const inputClass = 'w-full rounded-md border border-primary/25 bg-primary/5 px-3 py-2 text-sm focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white';
</script>

<svelte:head>
	<title>ARM - Settings</title>
</svelte:head>

<!-- Reusable snippet for a single ARM config field -->
{#snippet armField(key: string)}
	{@const val = armForm[key] ?? ''}
	{@const comment = getComment(key)}
	{@const dirty = isFieldDirty(key)}
	<div class="relative {dirty ? 'rounded-lg ring-2 ring-primary/40 dark:ring-primary/50' : ''}">
		<div class="{dirty ? 'px-3 py-3' : ''}">
			<div class="mb-1 flex items-center gap-1">
				<label for="arm-{key}" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
					{ARM_LABELS[key]?.label ?? key}
				</label>
				{#if dirty}
					<span class="ml-1 h-1.5 w-1.5 rounded-full bg-primary" title="Modified"></span>
				{/if}
				<button
					type="button"
					onclick={() => toggleInfo(key)}
					class="inline-flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold
						{armInfoKeys.has(key)
						? 'bg-primary-light-bg text-primary-text dark:bg-primary-light-bg-dark/40 dark:text-primary-text-dark'
						: 'bg-primary/10 text-gray-500 dark:bg-primary/15 dark:text-gray-400'}
						hover:bg-primary/20 dark:hover:bg-primary/20"
					title={key}
				>i</button>
			</div>
			{#if armInfoKeys.has(key)}
				<p class="mb-1 text-xs font-mono text-gray-400">{key}</p>
			{/if}

			{#if SELECT_OPTIONS[key]}
				{@const opts = SELECT_OPTIONS[key]}
				{@const curVal = val?.toString() ?? ''}
				<select
					id="arm-{key}"
					class={inputClass}
					value={curVal}
					onchange={(e) => {
						armForm[key] = (e.target as HTMLSelectElement).value;
						if (key === 'METADATA_PROVIDER') metadataTestResult = null;
					}}
				>
					{#if curVal && !opts.includes(curVal)}
						<option value={curVal}>{curVal}</option>
					{/if}
					{#each opts as opt}
						<option value={opt}>{opt || '(None)'}</option>
					{/each}
				</select>
			{:else if isBoolStr(val?.toString())}
				<div class="flex items-center gap-2 mt-1">
					<button
						type="button"
						onclick={() => toggleBool(key)}
						class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out
							{val?.toString().toLowerCase() === 'true'
							? 'bg-primary'
							: 'bg-primary/30 dark:bg-primary/20'}"
						role="switch"
						aria-checked={val?.toString().toLowerCase() === 'true'}
						aria-label={key}
					>
						<span
							class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out
								{val?.toString().toLowerCase() === 'true'
								? 'translate-x-5'
								: 'translate-x-0'}"
						></span>
					</button>
					<span class="text-xs font-medium {val?.toString().toLowerCase() === 'true' ? 'text-primary-text dark:text-primary-text-dark' : 'text-gray-400'}">
						{val?.toString().toLowerCase() === 'true' ? 'Enabled' : 'Disabled'}
					</span>
				</div>
			{:else if HIDDEN_KEYS.has(key)}
				<div class="flex gap-1">
					<input
						id="arm-{key}"
						type={armRevealedKeys.has(key) ? 'text' : 'password'}
						class="flex-1 rounded-md border border-primary/25 bg-primary/5 px-3 py-2 text-sm focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white"
						value={val?.toString() ?? ''}
						oninput={(e) => (armForm[key] = (e.target as HTMLInputElement).value)}
					/>
					<button
						type="button"
						onclick={() => toggleReveal(key)}
						class="rounded-md border border-primary/25 px-2 py-2 text-xs text-gray-600 hover:bg-primary/10 dark:border-primary/30 dark:text-gray-400 dark:hover:bg-primary/15"
					>
						{armRevealedKeys.has(key) ? 'Hide' : 'Show'}
					</button>
					{#if isMetadataApiKey(key)}
						<button
							type="button"
							onclick={handleTestMetadata}
							disabled={metadataTesting}
							class="rounded-md border border-primary/25 px-2 py-2 text-xs font-medium text-primary-text hover:bg-primary/10 disabled:opacity-50 dark:border-primary/30 dark:text-primary-text-dark dark:hover:bg-primary/15"
						>
							{metadataTesting ? 'Testing...' : 'Test'}
						</button>
					{/if}
				</div>
				{#if isMetadataApiKey(key) && metadataTestResult}
					<p class="mt-1 text-xs font-medium {metadataTestResult.success ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
						{metadataTestResult.message}
					</p>
				{/if}
			{:else if isIntStr(val?.toString())}
				<input
					id="arm-{key}"
					type="number"
					class={inputClass}
					value={val?.toString() ?? ''}
					oninput={(e) => (armForm[key] = (e.target as HTMLInputElement).value)}
				/>
			{:else}
				<input
					id="arm-{key}"
					type="text"
					class={inputClass}
					value={val?.toString() ?? ''}
					oninput={(e) => (armForm[key] = (e.target as HTMLInputElement).value)}
				/>
			{/if}

			{#if ARM_LABELS[key]?.description}
				<p class="mt-1 text-xs text-gray-400">{@html ARM_LABELS[key].description}</p>
			{:else if comment}
				<p class="mt-1 text-xs text-gray-400">{comment}</p>
			{/if}

			{#if key.endsWith('_PATTERN') && settings?.naming_variables}
				{@const patternVars = Object.entries(settings.naming_variables).filter(([v]) => {
					if (key.startsWith('MUSIC_')) return ['title', 'year', 'artist', 'album', 'label'].includes(v);
					if (key.startsWith('TV_')) return ['title', 'year', 'season', 'episode', 'label', 'video_type'].includes(v);
					return ['title', 'year', 'label', 'video_type'].includes(v);
				})}
				<div class="mt-1.5 flex flex-wrap gap-1">
					{#each patternVars as [varName, varDesc]}
						<span
							class="inline-flex items-center rounded px-1.5 py-0.5 text-[11px] font-mono
								bg-primary/10 text-gray-600 dark:bg-primary/15 dark:text-gray-300
								cursor-default"
							title={varDesc}
						>{'{' + varName + '}'}</span>
					{/each}
				</div>
			{/if}
		</div>
	</div>
{/snippet}

<!-- Reusable snippet for GPU support cards -->
{#snippet gpuCards(gpu: Record<string, boolean>)}
	<section>
		<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">
			Hardware Encoding
		</h2>
		<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
			{#each HW_GROUPS as group}
				{@const available = hasAny(gpu, group.keys)}
				<div
					class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark"
				>
					<div class="mb-3 flex items-center gap-2">
						<span
							class="inline-flex h-5 w-5 items-center justify-center rounded-full text-xs font-bold {available
								? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400'
								: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400'}"
							>{available ? '\u2713' : '\u2717'}</span
						>
						<h3 class="font-semibold text-gray-900 dark:text-white">{group.label}</h3>
					</div>
					<ul class="space-y-1">
						{#each group.keys as key}
							<li class="flex items-center gap-2 text-sm">
								<span
									class="inline-flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold {gpu[key]
										? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400'
										: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400'}"
									>{gpu[key] ? '\u2713' : '\u2717'}</span
								>
								<span class="text-gray-600 dark:text-gray-400"
									>{GPU_LABELS[key] ?? key}</span
								>
							</li>
						{/each}
					</ul>
				</div>
			{/each}
		</div>
	</section>
{/snippet}

<div class="space-y-6 pb-20">
	<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>

	{#if error}
		<div
			class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400"
		>
			{error}
		</div>
	{:else if !settings}
		<div class="py-8 text-center text-gray-400">Loading...</div>
	{:else}
		<!-- Tab Bar -->
		{@const tabClass = (tab: string) => `whitespace-nowrap border-b-2 px-1 py-2.5 text-sm font-medium transition-colors ${activeTab === tab ? 'border-primary text-primary-text dark:border-primary-text-dark dark:text-primary-text-dark' : 'border-transparent text-gray-500 hover:border-primary/30 hover:text-gray-700 dark:text-gray-400 dark:hover:border-primary/30 dark:hover:text-gray-300'}`}
		<div class="border-b border-primary/20 dark:border-primary/20">
			<nav class="-mb-px flex gap-4" aria-label="Settings tabs">
				<button type="button" onclick={() => setTab('ripping')} class={tabClass('ripping')}>Ripping</button>
				<button type="button" onclick={() => setTab('music')} class={tabClass('music')}>Music</button>
				<button type="button" onclick={() => setTab('transcoding')} class={tabClass('transcoding')}>Transcoding</button>
				<button type="button" onclick={() => setTab('notifications')} class={tabClass('notifications')}>Notifications</button>
				<button type="button" onclick={() => setTab('drives')} class={tabClass('drives')}>Drives</button>
				<button type="button" onclick={() => setTab('appearance')} class={tabClass('appearance')}>Appearance</button>
				<button type="button" onclick={() => setTab('system')} class={tabClass('system')}>System</button>
			</nav>
		</div>

		<!-- Transcoding Tab -->
		{#if activeTab === 'transcoding'}
			<div class="rounded-lg border border-primary/30 bg-primary-light-bg px-4 py-3 text-sm text-primary-dark dark:border-primary/30 dark:bg-primary-light-bg-dark/20 dark:text-primary-text-dark">
				These settings configure the <strong>dedicated transcoder service</strong>, a separate GPU-accelerated container that handles all transcoding. ARM rips discs and notifies this service to transcode.
			</div>

			<!-- Service Status -->
			<section>
				<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Service Status</h2>
				<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
					<!-- Connection card -->
					<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
						<h3 class="mb-3 font-semibold text-gray-900 dark:text-white">Connection</h3>
						<button
							type="button"
							onclick={handleTestConnection}
							disabled={connTesting}
							class="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-on-primary hover:bg-primary-hover disabled:opacity-50 dark:bg-primary dark:hover:bg-primary-hover"
						>
							{connTesting ? 'Testing...' : 'Test Connection'}
						</button>
						{#if connResult}
							<ul class="mt-3 space-y-1.5">
								<li class="flex items-center gap-2 text-sm">
									<span class="inline-flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold {connResult.reachable ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400'}">{connResult.reachable ? '\u2713' : '\u2717'}</span>
									<span class="text-gray-600 dark:text-gray-400">Reachable</span>
								</li>
								{#if connResult.reachable}
									<li class="flex items-center gap-2 text-sm">
										<span class="inline-flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold {connResult.auth_ok ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400' : connResult.auth_required ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'}">{connResult.auth_ok ? '\u2713' : connResult.auth_required ? '\u2717' : '\u2014'}</span>
										<span class="text-gray-600 dark:text-gray-400">API key {connResult.auth_ok ? 'valid' : connResult.auth_required ? 'invalid or missing' : 'not required'}</span>
									</li>
									<li class="flex items-center gap-2 text-sm">
										<span class="inline-flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold {connResult.worker_running ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400'}">{connResult.worker_running ? '\u2713' : '!'}</span>
										<span class="text-gray-600 dark:text-gray-400">Worker {connResult.worker_running ? 'running' : 'stopped'} &middot; {connResult.queue_size} queued</span>
									</li>
								{/if}
								{#if connResult.error}
									<li class="text-xs text-red-600 dark:text-red-400">{connResult.error}</li>
								{/if}
							</ul>
						{/if}
					</div>

					<!-- Webhook card -->
					<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
						<h3 class="mb-3 font-semibold text-gray-900 dark:text-white">Webhook</h3>
						<div class="mb-3">
							<label for="webhook-secret" class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">Webhook Secret</label>
							<input
								id="webhook-secret"
								type="password"
								class={inputClass}
								placeholder="Enter secret to test..."
								bind:value={webhookSecret}
							/>
							<p class="mt-1 text-xs text-gray-400">Leave empty to test with the saved TRANSCODER_WEBHOOK_SECRET from arm.yaml.</p>
						</div>
						<button
							type="button"
							onclick={handleTestWebhook}
							disabled={webhookTesting}
							class="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-on-primary hover:bg-primary-hover disabled:opacity-50 dark:bg-primary dark:hover:bg-primary-hover"
						>
							{webhookTesting ? 'Testing...' : 'Test Webhook'}
						</button>
						{#if webhookResult}
							<ul class="mt-3 space-y-1.5">
								<li class="flex items-center gap-2 text-sm">
									<span class="inline-flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold {webhookResult.reachable ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400'}">{webhookResult.reachable ? '\u2713' : '\u2717'}</span>
									<span class="text-gray-600 dark:text-gray-400">Reachable</span>
								</li>
								{#if webhookResult.reachable}
									<li class="flex items-center gap-2 text-sm">
										<span class="inline-flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold {webhookResult.secret_ok ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400'}">{webhookResult.secret_ok ? '\u2713' : '\u2717'}</span>
										<span class="text-gray-600 dark:text-gray-400">Secret {webhookResult.secret_ok ? 'accepted' : webhookResult.secret_required ? 'rejected' : 'invalid'}</span>
									</li>
								{/if}
								{#if webhookResult.error}
									<li class="text-xs text-red-600 dark:text-red-400">{webhookResult.error}</li>
								{/if}
							</ul>
						{/if}
					</div>

					<!-- Authentication info card (full width) -->
					{#if settings.transcoder_auth_status}
						<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs md:col-span-2 dark:border-primary/20 dark:bg-surface-dark">
							<h3 class="mb-3 font-semibold text-gray-900 dark:text-white">Authentication</h3>
							<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
								<div class="flex items-center gap-2 text-sm">
									<span class="inline-flex h-5 w-5 items-center justify-center rounded-full text-xs font-bold {settings.transcoder_auth_status.require_api_auth ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'}">{settings.transcoder_auth_status.require_api_auth ? '\u2713' : '\u2014'}</span>
									<span class="text-gray-700 dark:text-gray-300">API authentication {settings.transcoder_auth_status.require_api_auth ? 'enabled' : 'disabled'}</span>
								</div>
								<div class="flex items-center gap-2 text-sm">
									<span class="inline-flex h-5 w-5 items-center justify-center rounded-full text-xs font-bold {settings.transcoder_auth_status.webhook_secret_configured ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400' : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'}">{settings.transcoder_auth_status.webhook_secret_configured ? '\u2713' : '\u2014'}</span>
									<span class="text-gray-700 dark:text-gray-300">Webhook secret {settings.transcoder_auth_status.webhook_secret_configured ? 'configured' : 'not configured'}</span>
								</div>
							</div>
							<p class="mt-3 text-xs text-gray-400">API authentication is configured via Docker environment variables (REQUIRE_API_AUTH, API_KEY) on the transcoder container. The webhook secret is set in Notifications &gt; Transcoder and must match WEBHOOK_SECRET on the transcoder.</p>
						</div>
					{/if}
				</div>
			</section>

			{#if settings.transcoder_gpu_support}
				{@render gpuCards(settings.transcoder_gpu_support)}
			{/if}

			{#if settings.transcoder_config?.config}
				<section>
					<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">
						Configuration
					</h2>

					<div
						class="space-y-4 rounded-lg border border-primary/20 bg-surface p-4 dark:border-primary/20 dark:bg-surface-dark"
					>
						<!-- Encoding sub-panel -->
						<div class="space-y-4 rounded-md border border-primary/15 bg-page p-4 dark:border-primary/20 dark:bg-primary/5">
							<h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Video Encoding</h3>

							<!-- Video Encoder -->
							<div class="relative {isTcFieldDirty('video_encoder') ? 'rounded-lg ring-2 ring-primary/40 dark:ring-primary/50' : ''}">
								<div class="{isTcFieldDirty('video_encoder') ? 'px-3 py-3' : ''}">
									<div class="mb-1 flex items-center gap-1">
										<label for="tc-video_encoder" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
											{TC_LABELS['video_encoder'] ?? 'Video Encoder'}
										</label>
										{#if isTcFieldDirty('video_encoder')}
											<span class="ml-1 h-1.5 w-1.5 rounded-full bg-primary" title="Modified"></span>
										{/if}
									</div>
									<select
										id="tc-video_encoder"
										class={inputClass}
										bind:value={tcForm.video_encoder}
									>
										{#each VIDEO_ENCODER_OPTIONS as enc}
											<option value={enc.value}>{enc.label}</option>
										{/each}
									</select>
									{#if TC_HELP['video_encoder']}
										<p class="mt-1 text-xs text-gray-400">{TC_HELP['video_encoder']}</p>
									{/if}
								</div>
							</div>

							<!-- Preset dropdowns (3-column row) -->
							<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
								{#each TC_PRESET_KEYS as key}
									{@const selectOpts = tcSelectOptions(key)}
									<div class="relative {isTcFieldDirty(key) ? 'rounded-lg ring-2 ring-primary/40 dark:ring-primary/50' : ''}">
										<div class="{isTcFieldDirty(key) ? 'px-3 py-3' : ''}">
											<div class="mb-1 flex items-center gap-1">
												<label for="tc-{key}" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
													{TC_LABELS[key] ?? key}
												</label>
												{#if isTcFieldDirty(key)}
													<span class="ml-1 h-1.5 w-1.5 rounded-full bg-primary" title="Modified"></span>
												{/if}
											</div>
											{#if selectOpts}
												<select
													id="tc-{key}"
													class={inputClass}
													bind:value={tcForm[key]}
												>
													{#each selectOpts as opt}
														<option value={opt}>{opt || '(None)'}</option>
													{/each}
												</select>
											{:else}
												<input
													id="tc-{key}"
													type="text"
													class={inputClass}
													bind:value={tcForm[key]}
												/>
											{/if}
											{#if TC_HELP[key]}
												<p class="mt-1 text-xs text-gray-400">{TC_HELP[key]}</p>
											{/if}
										</div>
									</div>
								{/each}
							</div>

							<!-- Custom Preset File (full width, last) -->
							{#if tcSelectOptions('handbrake_preset_file')}
								{@const pfOpts = tcSelectOptions('handbrake_preset_file')}
								<div class="relative {isTcFieldDirty('handbrake_preset_file') ? 'rounded-lg ring-2 ring-primary/40 dark:ring-primary/50' : ''}">
									<div class="{isTcFieldDirty('handbrake_preset_file') ? 'px-3 py-3' : ''}">
										<div class="mb-1 flex items-center gap-1">
											<label for="tc-handbrake_preset_file" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
												{TC_LABELS['handbrake_preset_file']}
											</label>
											{#if isTcFieldDirty('handbrake_preset_file')}
												<span class="ml-1 h-1.5 w-1.5 rounded-full bg-primary" title="Modified"></span>
											{/if}
										</div>
										<select
											id="tc-handbrake_preset_file"
											class={inputClass}
											value={tcForm.handbrake_preset_file ?? ''}
											onchange={(e) => handlePresetFileChange(e.currentTarget.value)}
										>
											{#each pfOpts as opt}
												<option value={opt}>{opt || '(None)'}</option>
											{/each}
										</select>
										{#if TC_HELP['handbrake_preset_file']}
											<p class="mt-1 text-xs text-gray-400">{TC_HELP['handbrake_preset_file']}</p>
										{/if}
									</div>
								</div>
							{/if}

							<!-- Audio & Subtitle streams (part of video transcode) -->
							<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
								{#each ['audio_encoder', 'subtitle_mode'] as key}
									{@const selectOpts = tcSelectOptions(key)}
									<div class="relative {isTcFieldDirty(key) ? 'rounded-lg ring-2 ring-primary/40 dark:ring-primary/50' : ''}">
										<div class="{isTcFieldDirty(key) ? 'px-3 py-3' : ''}">
											<div class="mb-1 flex items-center gap-1">
												<label for="tc-{key}" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
													{TC_LABELS[key] ?? key}
												</label>
												{#if isTcFieldDirty(key)}
													<span class="ml-1 h-1.5 w-1.5 rounded-full bg-primary" title="Modified"></span>
												{/if}
											</div>
											{#if selectOpts}
												<select
													id="tc-{key}"
													class={inputClass}
													bind:value={tcForm[key]}
												>
													{#each selectOpts as opt}
														<option value={opt}>{opt}</option>
													{/each}
												</select>
											{:else}
												<input
													id="tc-{key}"
													type="text"
													class={inputClass}
													bind:value={tcForm[key]}
												/>
											{/if}
										</div>
									</div>
								{/each}
							</div>
						</div>

						<!-- Directories sub-panel -->
						<div class="space-y-4 rounded-md border border-primary/15 bg-page p-4 dark:border-primary/20 dark:bg-primary/5">
							<h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Output Directories</h3>
							{#if tcPaths}
								<div class="grid grid-cols-1 gap-2 text-xs md:grid-cols-3">
									<div class="rounded-sm bg-primary/10 px-2 py-1 dark:bg-primary/15">
										<span class="font-medium text-gray-500 dark:text-gray-400">Raw:</span>
										<span class="ml-1 font-mono text-gray-700 dark:text-gray-200">{tcPaths.raw_path}</span>
									</div>
									<div class="rounded-sm bg-primary/10 px-2 py-1 dark:bg-primary/15">
										<span class="font-medium text-gray-500 dark:text-gray-400">Completed:</span>
										<span class="ml-1 font-mono text-gray-700 dark:text-gray-200">{tcPaths.completed_path}</span>
									</div>
									<div class="rounded-sm bg-primary/10 px-2 py-1 dark:bg-primary/15">
										<span class="font-medium text-gray-500 dark:text-gray-400">Work:</span>
										<span class="ml-1 font-mono text-gray-700 dark:text-gray-200">{tcPaths.work_path}</span>
									</div>
								</div>
							{/if}
							<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
								{#each ['movies_subdir', 'tv_subdir', 'audio_subdir'] as key}
									<div class="relative {isTcFieldDirty(key) ? 'rounded-lg ring-2 ring-primary/40 dark:ring-primary/50' : ''}">
										<div class="{isTcFieldDirty(key) ? 'px-3 py-3' : ''}">
											<div class="mb-1 flex items-center gap-1">
												<label for="tc-{key}" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
													{TC_LABELS[key] ?? key}
												</label>
												{#if isTcFieldDirty(key)}
													<span class="ml-1 h-1.5 w-1.5 rounded-full bg-primary" title="Modified"></span>
												{/if}
											</div>
											<input
												id="tc-{key}"
												type="text"
												class={inputClass}
												bind:value={tcForm[key]}
											/>
											{#if tcPaths}
												<p class="mt-1 text-xs font-mono text-gray-400">
													{tcPaths.completed_path}/{tcForm[key]}
												</p>
											{/if}
										</div>
									</div>
								{/each}
							</div>
							<div class="relative {isTcFieldDirty('delete_source') ? 'rounded-lg ring-2 ring-primary/40 dark:ring-primary/50' : ''}">
								<div class="{isTcFieldDirty('delete_source') ? 'px-3 py-3' : ''}">
									<label
										for="tc-delete_source"
										class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
									>
										{TC_LABELS['delete_source'] ?? 'Delete Source'}
									</label>
									<div class="flex items-center gap-2 mt-1">
										<button
											type="button"
											onclick={() => (tcForm.delete_source = !tcForm.delete_source)}
											class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out
												{tcForm.delete_source ? 'bg-primary' : 'bg-primary/30 dark:bg-primary/20'}"
											role="switch"
											aria-checked={!!tcForm.delete_source}
											aria-label="Delete Source After Transcode"
										>
											<span
												class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out
													{tcForm.delete_source ? 'translate-x-5' : 'translate-x-0'}"
											></span>
										</button>
										<span class="text-xs font-medium {tcForm.delete_source ? 'text-primary-text dark:text-primary-text-dark' : 'text-gray-400'}">
											{tcForm.delete_source ? 'Enabled' : 'Disabled'}
										</span>
									</div>
								</div>
							</div>
						</div>

						<!-- Operational settings -->
						{#if settings.transcoder_config.updatable_keys.filter((k) => !TC_PRESET_SET.has(k)).length > 0}
							<div class="space-y-4 rounded-md border border-primary/15 bg-page p-4 dark:border-primary/20 dark:bg-primary/5">
								<h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Operational</h3>
								<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
									{#each settings.transcoder_config.updatable_keys.filter((k) => !TC_PRESET_SET.has(k)) as key}
										{@const selectOpts = tcSelectOptions(key)}
										<div class="relative {isTcFieldDirty(key) ? 'rounded-lg ring-2 ring-primary/40 dark:ring-primary/50' : ''}">
											<div class="{isTcFieldDirty(key) ? 'px-3 py-3' : ''}">
												<div class="mb-1 flex items-center gap-1">
													<label for="tc-{key}" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
														{TC_LABELS[key] ?? key}
													</label>
													{#if isTcFieldDirty(key)}
														<span class="ml-1 h-1.5 w-1.5 rounded-full bg-primary" title="Modified"></span>
													{/if}
												</div>

												{#if selectOpts}
													<select
														id="tc-{key}"
														class={inputClass}
														bind:value={tcForm[key]}
													>
														{#each selectOpts as opt}
															<option value={opt}>{opt}</option>
														{/each}
													</select>
												{:else if TC_BOOL_KEYS.has(key)}
													<div class="flex items-center gap-2 mt-1">
														<button
															type="button"
															onclick={() => (tcForm[key] = !tcForm[key])}
															class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out
																{tcForm[key] ? 'bg-primary' : 'bg-primary/30 dark:bg-primary/20'}"
															role="switch"
															aria-checked={!!tcForm[key]}
															aria-label={TC_LABELS[key] ?? key}
														>
															<span
																class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out
																	{tcForm[key] ? 'translate-x-5' : 'translate-x-0'}"
															></span>
														</button>
														<span class="text-xs font-medium {tcForm[key] ? 'text-primary-text dark:text-primary-text-dark' : 'text-gray-400'}">
															{tcForm[key] ? 'Enabled' : 'Disabled'}
														</span>
													</div>
												{:else if TC_NUMBER_FIELDS[key]}
													{@const range = TC_NUMBER_FIELDS[key]}
													<input
														id="tc-{key}"
														type="number"
														min={range[0]}
														max={range[1]}
														step={range[2] ?? 1}
														class={inputClass}
														bind:value={tcForm[key]}
													/>
												{:else}
													<input
														id="tc-{key}"
														type="text"
														class={inputClass}
														bind:value={tcForm[key]}
													/>
												{/if}

												{#if TC_HELP[key]}
													<p class="mt-1 text-xs text-gray-400">{TC_HELP[key]}</p>
												{/if}
											</div>
										</div>
									{/each}
								</div>
							</div>
						{/if}
					</div>
				</section>
			{:else}
				<p class="text-sm text-gray-400">Transcoder offline or not configured.</p>
			{/if}
		{/if}

		<!-- Reusable ARM settings renderer -->
		{#snippet armSettingsSection(tabKey: string, includeUnmapped?: boolean)}
			{#if settings?.arm_config}
				{@const groups = getArmGroups(settings.arm_config, TAB_ARM_GROUPS[tabKey] ?? [], includeUnmapped ?? false)}
				{#if groups.length === 0 && armSearch}
					<p class="py-4 text-center text-sm text-gray-400">No settings match "{armSearch}"</p>
				{:else}
					<div class="space-y-2">
						{#each groups as group}
							<div id="panel-{group.label.toLowerCase().replace(/[^a-z0-9]+/g, '-')}" class="rounded-lg border border-primary/20 bg-surface dark:border-primary/20 dark:bg-surface-dark">
								<button
									type="button"
									onclick={() => toggleCollapse(group.label)}
									class="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold text-gray-900 hover:bg-page dark:text-white dark:hover:bg-primary/10"
								>
									<span>{group.label}</span>
									<svg
										class="h-4 w-4 transform transition-transform {armCollapsed[group.label] ? '' : 'rotate-180'}"
										fill="none" stroke="currentColor" viewBox="0 0 24 24"
									>
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
									</svg>
								</button>
								{#if !armCollapsed[group.label] || armSearch}
									<div class="border-t border-primary/20 px-4 py-3 dark:border-primary/20">
										<div class="space-y-4">
											{#each group.subpanels as subpanel}
												{#if subpanel.label}
													<div class="space-y-4 rounded-md border border-primary/15 bg-page p-4 dark:border-primary/20 dark:bg-primary/5">
														<h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">{subpanel.label}</h3>
														<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
															{#each subpanel.keys as key}
																{#if !isMetadataKeyHidden(key)}
																	{@render armField(key)}
																{/if}
															{/each}
														</div>
													</div>
												{:else}
													<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
														{#each subpanel.keys as key}
															{#if !isMetadataKeyHidden(key)}
																{@render armField(key)}
															{/if}
														{/each}
													</div>
												{/if}
											{/each}
										</div>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{/if}
			{:else}
				<p class="text-sm text-gray-400">No ARM configuration found.</p>
			{/if}
		{/snippet}

		<!-- Search bar snippet (shared across ARM-backed tabs) -->
		{#snippet armSearchBar()}
			<div class="relative">
				<svg class="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
				<input
					type="text"
					placeholder="Filter settings..."
					class="w-56 rounded-md border border-primary/25 bg-primary/5 py-1.5 pl-8 pr-3 text-sm focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white dark:placeholder-gray-500"
					bind:value={armSearch}
				/>
				{#if armSearch}
					<button
						type="button"
						onclick={() => (armSearch = '')}
						aria-label="Clear search"
						class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
					>
						<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				{/if}
			</div>
		{/snippet}

		<!-- Ripping Tab -->
		{#if activeTab === 'ripping'}
			<section>
				<div class="mb-3 flex items-center justify-between gap-3">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Ripping</h2>
					{@render armSearchBar()}
				</div>
				{@render armSettingsSection('ripping')}
			</section>
		{/if}

		<!-- Music Tab -->
		{#if activeTab === 'music'}
			<section>
				<div class="mb-3 flex items-center justify-between gap-3">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Music</h2>
					{@render armSearchBar()}
				</div>
				{@render armSettingsSection('music')}
			</section>

			<!-- Encoding & abcde.conf -->
			<section class="mt-2">
				<div class="rounded-lg border border-primary/20 bg-surface dark:border-primary/20 dark:bg-surface-dark">
					<button
						type="button"
						onclick={() => (abcdeCollapsed = !abcdeCollapsed)}
						class="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold text-gray-900 hover:bg-page dark:text-white dark:hover:bg-primary/10"
					>
						<span>Encoding</span>
						<svg
							class="h-4 w-4 transform transition-transform {abcdeCollapsed ? '' : 'rotate-180'}"
							fill="none" stroke="currentColor" viewBox="0 0 24 24"
						>
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
						</svg>
					</button>
					{#if !abcdeCollapsed}
						<div class="border-t border-primary/20 px-4 py-3 dark:border-primary/20">
							<!-- ARM encoding fields -->
							{#if settings?.arm_config}
								<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
									{#each ['AUDIO_FORMAT', 'ABCDE_CONFIG_FILE'] as key}
										{#if settings.arm_config[key] !== undefined}
											{@render armField(key)}
										{/if}
									{/each}
								</div>
							{/if}

							<!-- abcde.conf file editor -->
							<div class="mt-4">
								<div class="mb-2 flex items-center justify-between gap-3">
									<h4 class="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
										abcde.conf
										{#if abcdePath}
											<span class="ml-1 font-normal normal-case tracking-normal text-gray-400">{abcdePath}</span>
										{/if}
									</h4>
									{#if abcdeExists || abcdeDirty}
										<div class="flex items-center gap-1.5">
											<div class="relative">
												<svg class="pointer-events-none absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
												</svg>
												<input
													type="text"
													placeholder="Search..."
													class="w-44 rounded-md border border-primary/25 bg-primary/5 py-1 pl-7 pr-2 text-xs focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white dark:placeholder-gray-500"
													bind:value={abcdeSearch}
													onkeydown={(e) => { if (e.key === 'Enter') { e.preventDefault(); abcdeSearchNav(e.shiftKey ? -1 : 1); } }}
												/>
											</div>
											{#if abcdeSearch}
												<span class="text-xs text-gray-400 tabular-nums">{abcdeMatches.length > 0 ? `${abcdeSearchIndex + 1}/${abcdeMatches.length}` : '0'}</span>
												<button type="button" onclick={() => abcdeSearchNav(-1)} disabled={abcdeMatches.length === 0} class="rounded p-0.5 text-gray-400 hover:text-gray-600 disabled:opacity-30 dark:hover:text-gray-300" aria-label="Previous match">
													<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>
												</button>
												<button type="button" onclick={() => abcdeSearchNav(1)} disabled={abcdeMatches.length === 0} class="rounded p-0.5 text-gray-400 hover:text-gray-600 disabled:opacity-30 dark:hover:text-gray-300" aria-label="Next match">
													<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
												</button>
											{/if}
										</div>
									{/if}
								</div>
								{#if abcdeLoading}
									<p class="py-4 text-center text-sm text-gray-400">Loading abcde.conf...</p>
								{:else if !abcdeLoaded}
									<p class="py-4 text-center text-sm text-gray-400">Failed to load abcde.conf</p>
								{:else if !abcdeExists && !abcdeDirty}
									<div class="rounded-md border border-primary/15 bg-page p-6 text-center dark:border-primary/20 dark:bg-primary/5">
										<p class="text-sm text-gray-500 dark:text-gray-400">
											No abcde.conf file found at <code class="rounded bg-gray-200 px-1 py-0.5 font-mono text-xs dark:bg-gray-700">{abcdePath}</code>
										</p>
										<p class="mt-1 text-xs text-gray-400 dark:text-gray-500">Start typing below to create one.</p>
									</div>
									<textarea
										bind:this={abcdeTextarea}
										class="mt-3 w-full rounded-md border border-primary/25 bg-primary/5 p-3 font-mono text-sm leading-relaxed focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white dark:placeholder-gray-500"
										rows="10"
										placeholder="# abcde.conf — paste or type your configuration here"
										bind:value={abcdeContent}
									></textarea>
								{:else}
									<textarea
										bind:this={abcdeTextarea}
										class="w-full rounded-md border border-primary/25 bg-primary/5 p-3 font-mono text-sm leading-relaxed focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white dark:placeholder-gray-500"
										rows="20"
										bind:value={abcdeContent}
									></textarea>
								{/if}

								{#if abcdeDirty || abcdeFeedback}
									<div class="mt-3 flex items-center gap-3">
										{#if abcdeDirty}
											<button
												type="button"
												onclick={handleAbcdeSave}
												disabled={abcdeSaving}
												class="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-white shadow-xs hover:bg-primary/80 disabled:opacity-50"
											>
												{abcdeSaving ? 'Saving...' : 'Save'}
											</button>
											<button
												type="button"
												onclick={handleAbcdeDiscard}
												class="rounded-md border border-primary/25 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-page dark:border-primary/30 dark:text-gray-300 dark:hover:bg-primary/10"
											>
												Discard
											</button>
										{/if}
										{#if abcdeFeedback}
											<span class="text-sm {abcdeFeedback.type === 'success' ? 'text-green-500' : 'text-red-500'}">
												{abcdeFeedback.message}
											</span>
										{/if}
									</div>
								{/if}
							</div>
						</div>
					{/if}
				</div>
			</section>
		{/if}

		<!-- Notifications Tab -->
		{#if activeTab === 'notifications'}
			<section>
				<div class="mb-3 flex items-center justify-between gap-3">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Notifications</h2>
					{@render armSearchBar()}
				</div>
				{@render armSettingsSection('notifications')}
			</section>
		{/if}

		<!-- System Info Tab -->
		{#if activeTab === 'system'}
			{#if systemInfoLoading}
				<div class="py-8 text-center text-gray-400">Loading system info...</div>
			{:else if systemInfo}
				<div class="space-y-6">
					<!-- Versions -->
					<section>
						<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Versions</h2>
						<div class="grid grid-cols-2 gap-4 md:grid-cols-5">
							{#each Object.entries(systemInfo.versions) as [name, version]}
								<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
									<p class="text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">{name}</p>
									<div class="mt-1 flex items-center gap-2">
										<div class="h-2 w-2 rounded-full {version === 'offline' ? 'bg-red-400' : version === 'unknown' ? 'bg-gray-400' : 'bg-green-400'}"></div>
										<p class="text-sm font-semibold text-gray-900 dark:text-white">{version}</p>
									</div>
								</div>
							{/each}
						</div>
					</section>

					<!-- Service Endpoints -->
					{#if systemInfo.endpoints}
						<section>
							<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Service Endpoints</h2>
							<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
								{#each Object.entries(systemInfo.endpoints) as [name, ep]}
									{@const envVar = name === 'arm' ? 'ARM_UI_ARM_URL' : name === 'transcoder' ? 'ARM_UI_TRANSCODER_URL' : name.toUpperCase() + '_URL'}
								<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
										<div class="flex items-center justify-between">
											<p class="text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">{name}</p>
											<span class="inline-flex items-center gap-1.5 text-xs font-medium {ep.reachable ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
												<div class="h-2 w-2 rounded-full {ep.reachable ? 'bg-green-500' : 'bg-red-500'}"></div>
												{ep.reachable ? 'Reachable' : 'Unreachable'}
											</span>
										</div>
										<div class="mt-2 flex items-center gap-2">
											<p class="font-mono text-sm text-gray-900 dark:text-white">{ep.url}</p>
											<button
												type="button"
												onclick={() => toggleEndpointInfo(name)}
												class="inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold
													{endpointInfoKeys.has(name)
													? 'bg-primary-light-bg text-primary-text dark:bg-primary-light-bg-dark/40 dark:text-primary-text-dark'
													: 'bg-primary/10 text-gray-500 dark:bg-primary/15 dark:text-gray-400'}
													hover:bg-primary/20 dark:hover:bg-primary/20"
												title={envVar}
											>i</button>
										</div>
										{#if endpointInfoKeys.has(name)}
											<p class="mt-1 font-mono text-xs text-gray-400 dark:text-gray-500">{envVar}</p>
										{/if}
									</div>
								{/each}
							</div>
						</section>
					{/if}

					<!-- Paths -->
					{#if systemInfo.paths.length > 0}
						<section>
							<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Paths</h2>
							<div class="overflow-x-auto rounded-lg border border-primary/20 dark:border-primary/20">
								<table class="w-full text-left text-sm">
									<thead class="bg-page text-gray-600 dark:bg-primary/5 dark:text-gray-400">
										<tr>
											<th class="px-4 py-3 font-medium">Setting</th>
											<th class="px-4 py-3 font-medium">Path</th>
											<th class="px-4 py-3 font-medium">Status</th>
										</tr>
									</thead>
									<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
										{#each systemInfo.paths as p}
											<tr class="hover:bg-page dark:hover:bg-gray-800/50">
												<td class="px-4 py-2 font-mono text-xs font-medium text-gray-500 dark:text-gray-400">{p.setting}</td>
												<td class="px-4 py-2 font-mono text-xs text-gray-900 dark:text-white">{p.path}</td>
												<td class="px-4 py-2">
													{#if !p.exists}
														<span class="inline-flex items-center gap-1 text-xs text-red-500">
															<svg class="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" /></svg>
															Missing
														</span>
													{:else if p.writable}
														<span class="inline-flex items-center gap-1 text-xs text-green-500">
															<svg class="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" /></svg>
															OK
														</span>
													{:else}
														<span class="inline-flex items-center gap-1 text-xs text-amber-500">
															<svg class="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
															Read-only
														</span>
													{/if}
												</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						</section>
					{/if}

					<!-- Database -->
					<section>
						<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Database</h2>
						<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
							<dl class="grid grid-cols-3 gap-4 text-sm">
								<div>
									<dt class="text-gray-500 dark:text-gray-400">Path</dt>
									<dd class="mt-1 font-mono text-xs text-gray-900 dark:text-white">{systemInfo.database.path}</dd>
								</div>
								<div>
									<dt class="text-gray-500 dark:text-gray-400">Size</dt>
									<dd class="mt-1 font-medium text-gray-900 dark:text-white">{systemInfo.database.size_bytes != null ? formatBytes(systemInfo.database.size_bytes) : 'N/A'}</dd>
								</div>
								<div>
									<dt class="text-gray-500 dark:text-gray-400">Status</dt>
									<dd class="mt-1">
										<span class="inline-flex items-center gap-1.5 text-sm font-medium {systemInfo.database.available ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
											<div class="h-2 w-2 rounded-full {systemInfo.database.available ? 'bg-green-500' : 'bg-red-500'}"></div>
											{systemInfo.database.available ? 'Connected' : 'Unavailable'}
										</span>
									</dd>
								</div>
							</dl>
						</div>
					</section>

					<!-- Drives link -->
					<section class="flex items-center gap-2">
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Drives</h2>
						<button
							type="button"
							onclick={() => setTab('drives')}
							class="text-sm text-primary hover:text-primary-hover hover:underline dark:text-primary dark:hover:text-primary-hover"
						>
							View in Drives tab
						</button>
					</section>
				</div>
			{:else}
				<p class="py-8 text-center text-gray-400">Failed to load system info.</p>
			{/if}

			<!-- Editable ARM system settings below diagnostics -->
			<section>
				<div class="mb-3 flex items-center justify-between gap-3">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Configuration</h2>
					{@render armSearchBar()}
				</div>
				{@render armSettingsSection('system', true)}
			</section>
		{/if}

		<!-- Appearance Tab -->
		{#if activeTab === 'appearance'}
			<section class="space-y-6">
				<!-- Color Scheme -->
				<div class="rounded-lg border border-primary/20 bg-surface p-6 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
					<h2 class="mb-1 text-lg font-semibold text-gray-900 dark:text-white">Color Scheme</h2>
					<p class="mb-4 text-sm text-gray-500 dark:text-gray-400">Choose an accent color for buttons, links, and highlights throughout the UI.</p>
					<div class="flex flex-wrap gap-3">
						{#each COLOR_SCHEMES as scheme}
							<button
								type="button"
								onclick={() => ($colorScheme = scheme.id)}
								class="flex flex-col items-center gap-1.5 rounded-lg border-2 px-4 py-3 transition-colors
									{$colorScheme === scheme.id
									? 'border-primary bg-primary-light-bg dark:border-primary-text-dark dark:bg-primary-light-bg-dark/20'
									: 'border-primary/15 hover:border-primary/30 dark:border-primary/15 dark:hover:border-primary/30'}"
							>
								<span class="h-8 w-8 rounded-full {scheme.swatch}"></span>
								<span class="text-xs font-medium text-gray-700 dark:text-gray-300">{scheme.label}</span>
							</button>
						{/each}
					</div>
				</div>

				<!-- Dark Mode -->
				<div class="rounded-lg border border-primary/20 bg-surface p-6 shadow-xs dark:border-primary/20 dark:bg-surface-dark">
					<div class="flex items-center justify-between">
						<div>
							<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Dark Mode</h2>
							{#if $schemeLocksMode}
								<p class="text-sm text-gray-500 dark:text-gray-400">Locked by theme</p>
							{:else}
								<p class="text-sm text-gray-500 dark:text-gray-400">Toggle between light and dark mode.</p>
							{/if}
						</div>
						{#if !$schemeLocksMode}
							<div class="flex items-center gap-2">
								<button
									type="button"
									onclick={toggleTheme}
									class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out
										{$theme === 'dark' ? 'bg-primary' : 'bg-primary/30 dark:bg-primary/20'}"
									role="switch"
									aria-checked={$theme === 'dark'}
									aria-label="Dark mode"
								>
									<span
										class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out
											{$theme === 'dark' ? 'translate-x-5' : 'translate-x-0'}"
									></span>
								</button>
								<span class="text-xs font-medium {$theme === 'dark' ? 'text-primary-text dark:text-primary-text-dark' : 'text-gray-400'}">
									{$theme === 'dark' ? 'On' : 'Off'}
								</span>
							</div>
						{/if}
					</div>
				</div>

				<!-- Feature request prompt -->
				<div class="flex justify-center pt-2">
					<span class="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-4 py-2 text-xs text-gray-500 dark:text-gray-400">
						<svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5.002 5.002 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
						Not seeing what you want? Submit your feature requests on GitHub.
					</span>
				</div>
			</section>
		{/if}

		{#if activeTab === 'drives'}
			<section class="space-y-6">
				{#if $driveError}
					<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
						{$driveError}
					</div>
				{:else if $drives.length === 0}
					<p class="py-8 text-center text-gray-400">No drives detected.</p>
				{:else}
					<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
						{#each $drives as drive (drive.drive_id)}
							<DriveCard {drive} onupdate={() => drives.refresh()} />
						{/each}
					</div>
				{/if}

				<!-- Diagnostics -->
				<div class="border-t border-primary/15 pt-4 dark:border-primary/20">
					<div class="flex items-center gap-3">
						<button
							onclick={runDiagnostic}
							disabled={diagRunning}
							class="inline-flex items-center gap-2 rounded-lg bg-blue-100 px-4 py-2 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-200 disabled:opacity-50 dark:bg-blue-900/30 dark:text-blue-400 dark:hover:bg-blue-900/50"
						>
							<svg class="h-4 w-4 {diagRunning ? 'animate-spin' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
							</svg>
							{diagRunning ? 'Running...' : 'Check Udev & Drives'}
						</button>
						{#if diagError}
							<span class="text-sm text-red-600 dark:text-red-400">{diagError}</span>
						{/if}
					</div>

					{#if diagResult}
						<div class="mt-4 space-y-3">
							<!-- Global issues -->
							{#if diagResult.issues.length > 0}
								<div class="rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-800 dark:bg-red-900/20">
									<p class="mb-1 text-xs font-semibold uppercase tracking-wide text-red-600 dark:text-red-400">System Issues</p>
									{#each diagResult.issues as issue}
										<p class="text-sm text-red-700 dark:text-red-300">{issue}</p>
									{/each}
								</div>
							{/if}

							<!-- Global status -->
							<div class="flex flex-wrap gap-3 text-sm">
								<span class="inline-flex items-center gap-1.5">
									<div class="h-2 w-2 rounded-full {diagResult.udevd_running ? 'bg-green-500' : 'bg-red-500'}"></div>
									<span class="text-gray-700 dark:text-gray-300">udevd {diagResult.udevd_running ? 'running' : 'not running'}</span>
								</span>
								<span class="text-gray-500 dark:text-gray-400">
									Kernel sees: {diagResult.kernel_drives.length > 0 ? diagResult.kernel_drives.join(', ') : 'none'}
								</span>
							</div>

							<!-- Per-drive diagnostics -->
							{#each diagResult.drives as diag}
								<div class="rounded-lg border p-3 {diag.issues.length > 0
									? 'border-amber-200 bg-amber-50/50 dark:border-amber-800/50 dark:bg-amber-900/10'
									: 'border-green-200 bg-green-50/50 dark:border-green-800/50 dark:bg-green-900/10'}">
									<div class="flex items-center justify-between">
										<span class="font-mono text-sm font-semibold text-gray-900 dark:text-white">/dev/{diag.devname}</span>
										<div class="flex items-center gap-2 text-xs">
											{#if diag.arm_processing}
												<span class="rounded-full bg-blue-100 px-2 py-0.5 font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">Processing</span>
											{/if}
											<span class="rounded-full px-2 py-0.5 font-medium
												{diag.tray_status === 4 ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
												: diag.tray_status === 1 ? 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
												: diag.tray_status === 2 ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
												: diag.tray_status === 3 ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
												: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'}">
												{diag.tray_status_name ?? 'unknown'}
											</span>
										</div>
									</div>

									<div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500 dark:text-gray-400">
										<span class="{diag.dev_node_exists ? '' : 'text-red-600 dark:text-red-400'}">
											dev: {diag.dev_node_exists ? 'yes' : 'MISSING'}
										</span>
										<span class="{diag.sysfs_exists ? '' : 'text-red-600 dark:text-red-400'}">
											sysfs: {diag.sysfs_exists ? 'yes' : 'MISSING'}
										</span>
										<span class="{diag.in_kernel_cdrom ? '' : 'text-amber-600 dark:text-amber-400'}">
											kernel: {diag.in_kernel_cdrom ? 'yes' : 'no'}
										</span>
										<span class="{diag.in_database ? '' : 'text-amber-600 dark:text-amber-400'}">
											DB: {diag.in_database ? 'yes' : 'no'}
										</span>
										{#if diag.major_minor}
											<span>maj:min {diag.major_minor}</span>
										{/if}
										{#if diag.udevadm.ID_BUS}
											<span>bus: {diag.udevadm.ID_BUS}</span>
										{/if}
									</div>

									{#if Object.keys(diag.udevadm).length > 0}
										<div class="mt-2 flex flex-wrap gap-1.5">
											{#if diag.udevadm.ID_CDROM_MEDIA === '1'}
												<span class="rounded-sm bg-green-100 px-1.5 py-0.5 text-[10px] font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">MEDIA PRESENT</span>
											{/if}
											{#if diag.udevadm.ID_CDROM_MEDIA_DVD === '1'}
												<span class="rounded-sm bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary-text dark:bg-primary/15 dark:text-primary-text-dark">DVD</span>
											{/if}
											{#if diag.udevadm.ID_CDROM_MEDIA_BD === '1'}
												<span class="rounded-sm bg-purple-100 px-1.5 py-0.5 text-[10px] font-medium text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">BD</span>
											{/if}
											{#if diag.udevadm.ID_CDROM_MEDIA_CD === '1'}
												<span class="rounded-sm bg-blue-100 px-1.5 py-0.5 text-[10px] font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">CD</span>
											{/if}
											{#if diag.udevadm.ID_FS_TYPE}
												<span class="rounded-sm bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-600 dark:bg-gray-800 dark:text-gray-400">FS: {diag.udevadm.ID_FS_TYPE}</span>
											{/if}
										</div>
									{/if}

									{#if diag.issues.length > 0}
										<div class="mt-2 space-y-0.5">
											{#each diag.issues as issue}
												<p class="text-xs text-amber-700 dark:text-amber-400">{issue}</p>
											{/each}
										</div>
									{/if}
								</div>
							{/each}
						</div>
					{/if}
				</div>
			</section>
		{/if}
	{/if}
</div>

<!-- Sticky save bar -->
{#if anyDirty}
	<div class="fixed bottom-0 left-0 right-0 z-50 border-t border-primary/30 bg-surface/95 shadow-lg backdrop-blur-sm dark:border-primary/30 dark:bg-surface-dark/95">
		<div class="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
			<div class="flex items-center gap-3">
				<span class="h-2 w-2 shrink-0 rounded-full bg-primary animate-pulse"></span>
				<span class="text-sm font-bold text-gray-700 dark:text-gray-300">Unsaved {dirtyTabLabel} changes</span>
				{#if anyFeedback}
					<span
						class="text-sm {anyFeedback.type === 'success'
							? 'text-green-600 dark:text-green-400'
							: 'text-red-600 dark:text-red-400'}"
					>
						{anyFeedback.message}
					</span>
				{/if}
			</div>
			<div class="flex items-center gap-2">
				<button
					type="button"
					onclick={handleDiscardAll}
					class="rounded-lg px-4 py-2 text-sm font-medium text-gray-600 ring-1 ring-gray-300 hover:bg-gray-100 dark:text-gray-400 dark:ring-gray-600 dark:hover:bg-gray-800"
				>
					Discard
				</button>
				<button
					type="button"
					onclick={handleSaveAll}
					disabled={anySaving}
					class="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-on-primary hover:bg-primary-hover disabled:opacity-50 dark:bg-primary dark:hover:bg-primary-hover"
				>
					{anySaving ? 'Saving...' : 'Save Changes'}
				</button>
			</div>
		</div>
	</div>
{/if}
