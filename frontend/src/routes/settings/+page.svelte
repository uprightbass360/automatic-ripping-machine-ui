<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchSettings, saveArmConfig, saveTranscoderConfig, testMetadataKey, testTranscoderConnection, testTranscoderWebhook, fetchBashScript, saveBashScript } from '$lib/api/settings';
	import type { ConnectionTestResult, WebhookTestResult, BashScriptInfo } from '$lib/api/settings';
	import type { SettingsData } from '$lib/types/arm';
	import { theme, toggleTheme } from '$lib/stores/theme';
	import { colorScheme, COLOR_SCHEMES } from '$lib/stores/colorScheme';

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
	let activeTab = $state<'arm' | 'transcoder' | 'appearance'>('arm');

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

	// --- Notification script state ---
	let scriptInfo = $state<BashScriptInfo | null>(null);
	let scriptLoading = $state(false);
	let scriptSaving = $state(false);
	let scriptFeedback = $state<{type: 'success' | 'error'; message: string} | null>(null);
	let scriptForm = $state({transcoder_url: '', webhook_secret: '', local_raw_path: '', shared_raw_path: ''});
	let showAdvanced = $state(false);
	let showScriptPreview = $state(false);
	let scriptLoaded = false;

	onMount(async () => {
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
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load settings';
		}
	});

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
		armDirty && tcDirty ? 'ARM & Transcoder' : armDirty ? 'ARM' : 'Transcoder'
	);

	// Transcoder base paths (read-only, for display in directories panel)
	let tcPaths = $derived(settings?.transcoder_config?.paths);

	// --- GPU support labels ---
	const GPU_LABELS: Record<string, string> = {
		handbrake_nvenc: 'HandBrake NVENC',
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
		{ label: 'Nvidia NVENC', keys: ['handbrake_nvenc', 'ffmpeg_nvenc_h265', 'ffmpeg_nvenc_h264'] },
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
		RIPMETHOD_DVD: { label: 'Rip Method (DVD)', description: 'Override rip method for DVDs' },
		RIPMETHOD_BR: { label: 'Rip Method (Blu-ray)', description: 'Override rip method for Blu-rays' },
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
		MAKEMKV_PERMA_KEY: { label: 'MakeMKV License Key', description: 'Permanent or beta registration key for MakeMKV' },
		DATA_RIP_PARAMETERS: { label: 'Data Rip Parameters', description: 'Extra parameters for data disc ripping' },
		MAX_CONCURRENT_MAKEMKVINFO: { label: 'Max Concurrent Disc Scans', description: 'Limit parallel makemkvinfo processes (0 = unlimited)' },
		AUTO_EJECT: { label: 'Auto-Eject After Rip', description: 'Eject the disc when ripping completes' },
		RIP_POSTER: { label: 'Download Poster', description: 'Save movie poster artwork during ripping' },
		// Transcoding
		SKIP_TRANSCODE: { label: 'Skip Transcoding', description: 'Keep original MakeMKV files without transcoding' },
		HB_PRESET_DVD: { label: 'HandBrake Preset (DVD)', description: 'HandBrake preset for DVD sources' },
		HB_PRESET_BD: { label: 'HandBrake Preset (Blu-ray)', description: 'HandBrake preset for Blu-ray sources' },
		DEST_EXT: { label: 'Output Extension', description: 'File extension for transcoded files (e.g. mkv, mp4)' },
		HANDBRAKE_CLI: { label: 'HandBrake CLI Path', description: 'Path to the HandBrakeCLI binary' },
		HANDBRAKE_LOCAL: { label: 'HandBrake Local Path', description: 'Path to a local HandBrake binary override' },
		HB_ARGS_DVD: { label: 'HandBrake Args (DVD)', description: 'Extra HandBrake arguments for DVD transcoding' },
		HB_ARGS_BD: { label: 'HandBrake Args (Blu-ray)', description: 'Extra HandBrake arguments for Blu-ray transcoding' },
		FFMPEG_CLI: { label: 'FFmpeg CLI Path', description: 'Path to the ffmpeg binary' },
		FFMPEG_LOCAL: { label: 'FFmpeg Local Path', description: 'Path to a local FFmpeg binary override' },
		FFMPEG_PRE_FILE_ARGS: { label: 'FFmpeg Pre-File Args', description: 'FFmpeg arguments inserted before the input file' },
		FFMPEG_POST_FILE_ARGS: { label: 'FFmpeg Post-File Args', description: 'FFmpeg arguments inserted after the input file' },
		USE_FFMPEG: { label: 'Use FFmpeg', description: 'Use FFmpeg instead of HandBrake for transcoding' },
		MAX_CONCURRENT_TRANSCODES: { label: 'Max Concurrent Transcodes', description: 'Limit parallel transcode processes (0 = unlimited)' },
		DELRAWFILES: { label: 'Delete Raw Files', description: 'Remove raw MakeMKV output after successful transcode' },
		// Music Ripping
		GET_AUDIO_TITLE: { label: 'Audio Metadata Source', description: 'none, musicbrainz, or freecddb for CD track info' },
		ABCDE_CONFIG_FILE: { label: 'abcde Config File', description: 'Path to the abcde configuration file for CD ripping' },
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
	};

	let armInfoKeys = $state<Set<string>>(new Set());

	function toggleInfo(key: string) {
		const next = new Set(armInfoKeys);
		if (next.has(key)) next.delete(key);
		else next.add(key);
		armInfoKeys = next;
	}

	// --- ARM config groups (explicit key-to-group mapping with sub-panels) ---
	const ARM_KEY_GROUPS: { label: string; subpanels: { label?: string; keys: string[] }[] }[] = [
		{ label: 'Video Ripping', subpanels: [
			{ label: 'Disc Identification', keys: ['VIDEOTYPE', 'GET_VIDEO_TITLE', 'ARM_CHECK_UDF', 'MANUAL_WAIT', 'MANUAL_WAIT_TIME'] },
			{ label: 'Track Selection', keys: ['MINLENGTH', 'MAXLENGTH', 'MAINFEATURE', 'PREVENT_99'] },
			{ label: 'Rip Method', keys: ['RIPMETHOD', 'RIPMETHOD_DVD', 'RIPMETHOD_BR', 'MKV_ARGS', 'DATA_RIP_PARAMETERS'] },
			{ label: 'MakeMKV', keys: ['MAKEMKV_PERMA_KEY', 'MAX_CONCURRENT_MAKEMKVINFO'] },
			{ label: 'Post-Rip Behavior', keys: ['ALLOW_DUPLICATES', 'AUTO_EJECT', 'RIP_POSTER'] },
		]},
		{ label: 'Transcoding', subpanels: [
			{ label: 'General', keys: ['SKIP_TRANSCODE', 'USE_FFMPEG', 'DEST_EXT', 'MAX_CONCURRENT_TRANSCODES', 'DELRAWFILES'] },
			{ label: 'HandBrake', keys: ['HB_PRESET_DVD', 'HB_PRESET_BD', 'HANDBRAKE_CLI', 'HANDBRAKE_LOCAL', 'HB_ARGS_DVD', 'HB_ARGS_BD'] },
			{ label: 'FFmpeg', keys: ['FFMPEG_CLI', 'FFMPEG_LOCAL', 'FFMPEG_PRE_FILE_ARGS', 'FFMPEG_POST_FILE_ARGS'] },
		]},
		{ label: 'Music Ripping', subpanels: [
			{ keys: ['GET_AUDIO_TITLE', 'ABCDE_CONFIG_FILE'] },
		]},
		{ label: 'Metadata', subpanels: [
			{ keys: ['METADATA_PROVIDER', 'OMDB_API_KEY', 'TMDB_API_KEY'] },
		]},
		{ label: 'General', subpanels: [
			{ keys: ['ARM_NAME', 'DISABLE_LOGIN', 'DATE_FORMAT', 'ARM_API_KEY'] },
		]},
		{ label: 'Web Server', subpanels: [
			{ keys: ['WEBSERVER_IP', 'WEBSERVER_PORT', 'UI_BASE_URL'] },
		]},
		{ label: 'Paths & Storage', subpanels: [
			{ label: 'Media Directories', keys: ['RAW_PATH', 'TRANSCODE_PATH', 'COMPLETED_PATH', 'EXTRAS_SUB'] },
			{ label: 'System Paths', keys: ['INSTALLPATH', 'LOGPATH', 'DBFILE', 'LOGLEVEL', 'LOGLIFE'] },
			{ label: 'File Permissions', keys: ['UMASK', 'SET_MEDIA_PERMISSIONS', 'CHMOD_VALUE', 'SET_MEDIA_OWNER', 'CHOWN_USER', 'CHOWN_GROUP'] },
		]},
		{ label: 'Emby', subpanels: [
			{ label: 'Connection', keys: ['EMBY_REFRESH', 'EMBY_SERVER', 'EMBY_PORT'] },
			{ label: 'Authentication', keys: ['EMBY_USERNAME', 'EMBY_USERID', 'EMBY_PASSWORD', 'EMBY_API_KEY'] },
			{ label: 'Client Identity', keys: ['EMBY_CLIENT', 'EMBY_DEVICE', 'EMBY_DEVICEID'] },
		]},
		{ label: 'Notifications', subpanels: [
			{ label: 'Triggers', keys: ['NOTIFY_RIP', 'NOTIFY_TRANSCODE', 'NOTIFY_JOBID'] },
			{ label: 'Services', keys: ['PB_KEY', 'IFTTT_KEY', 'IFTTT_EVENT', 'PO_USER_KEY', 'PO_APP_KEY'] },
			{ label: 'Custom / Apprise', keys: ['BASH_SCRIPT', 'JSON_URL', 'APPRISE'] },
		]},
	];

	// Structured sub-sections within HandBrake and FFmpeg subpanels (ARM Transcoding group)
	const TRANSCODING_SECTIONS: Record<string, { label: string; keys: string[] }[]> = {
		'HandBrake': [
			{ label: 'Presets', keys: ['HB_PRESET_DVD', 'HB_PRESET_BD'] },
			{ label: 'CLI Paths', keys: ['HANDBRAKE_CLI', 'HANDBRAKE_LOCAL'] },
			{ label: 'Extra Arguments', keys: ['HB_ARGS_DVD', 'HB_ARGS_BD'] },
		],
		'FFmpeg': [
			{ label: 'CLI Paths', keys: ['FFMPEG_CLI', 'FFMPEG_LOCAL'] },
			{ label: 'Arguments', keys: ['FFMPEG_PRE_FILE_ARGS', 'FFMPEG_POST_FILE_ARGS'] },
		],
	};

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

	// --- Cross-service derived state ---
	let skipTranscode = $derived(
		(armForm['SKIP_TRANSCODE'] ?? '').toString().toLowerCase() === 'true'
	);

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

	// --- Notification script ---
	async function loadScriptInfo() {
		if (scriptLoaded || scriptLoading) return;
		scriptLoading = true;
		try {
			scriptInfo = await fetchBashScript();
			if (scriptInfo.variables) {
				scriptForm = { ...scriptInfo.variables };
			} else {
				scriptForm.transcoder_url = scriptInfo.default_transcoder_url;
			}
			scriptLoaded = true;
		} catch {
			// silently fail — section will show loading state
		} finally {
			scriptLoading = false;
		}
	}

	$effect(() => {
		if (activeTab === 'transcoder') {
			loadScriptInfo();
		}
	});

	async function handleSaveScript() {
		scriptSaving = true;
		scriptFeedback = null;
		try {
			const result = await saveBashScript(scriptForm);
			if (result.success) {
				// Auto-fill BASH_SCRIPT in ARM config if empty or different
				const currentBashScript = armForm['BASH_SCRIPT'] ?? '';
				if (currentBashScript !== result.arm_path) {
					armForm['BASH_SCRIPT'] = result.arm_path;
				}
				scriptFeedback = { type: 'success', message: 'Script saved. Save ARM settings to apply BASH_SCRIPT path.' };
				// Refresh script info for preview
				scriptInfo = await fetchBashScript();
			}
		} catch (e) {
			scriptFeedback = { type: 'error', message: e instanceof Error ? e.message : 'Failed to save script' };
		} finally {
			scriptSaving = false;
			clearFeedback(() => (scriptFeedback = null));
		}
	}

	// HandBrake presets — loaded dynamically from the ARM container at startup.
	// Falls back to transcoder presets if the ARM init container hasn't run.
	let hbPresets = $derived(settings?.arm_handbrake_presets ?? []);

	// Combined preset list: ARM built-in presets, or transcoder custom presets as fallback
	let armPresets = $derived.by<string[]>(() => {
		if (hbPresets.length > 0) return hbPresets;
		return settings?.transcoder_config?.valid_handbrake_presets ?? [];
	});

	// SELECT_OPTIONS is derived so it picks up dynamic HB presets
	let SELECT_OPTIONS = $derived<Record<string, string[]>>({
		VIDEOTYPE: ['auto', 'series', 'movie'],
		RIPMETHOD: ['mkv', 'backup', 'backup_dvd'],
		LOGLEVEL: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
		METADATA_PROVIDER: ['omdb', 'tmdb'],
		GET_AUDIO_TITLE: ['none', 'musicbrainz', 'freecddb'],
		DEST_EXT: ['mkv', 'mp4', 'm4v'],
		...(armPresets.length > 0
			? { HB_PRESET_DVD: ['', ...armPresets], HB_PRESET_BD: ['', ...armPresets] }
			: {}),
	});

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

	function getArmGroups(config: Record<string, string | null>) {
		const allKeys = new Set(Object.keys(config));
		const mapped = new Set<string>();
		const groups: { label: string; subpanels: { label?: string; keys: string[] }[] }[] = [];

		for (const group of ARM_KEY_GROUPS) {
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

		// Catch-all for any unmapped keys (future-proofing)
		const unmapped = [...allKeys].filter((k) => !mapped.has(k) && matchesSearch(k));
		if (unmapped.length > 0) {
			groups.push({ label: 'Other', subpanels: [{ keys: unmapped }] });
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

	// Input class shared across all ARM fields
	const inputClass = 'w-full rounded-md border border-primary/25 bg-primary/5 px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white';
</script>

<svelte:head>
	<title>Settings - ARM UI</title>
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
						class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out
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
						class="flex-1 rounded-md border border-primary/25 bg-primary/5 px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white"
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
				<p class="mt-1 text-xs text-gray-400">{ARM_LABELS[key].description}</p>
			{:else if comment}
				<p class="mt-1 text-xs text-gray-400">{comment}</p>
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
					class="rounded-lg border border-primary/20 bg-surface p-4 shadow-sm dark:border-primary/20 dark:bg-surface-dark"
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
		<div class="border-b border-primary/20 dark:border-primary/20">
			<nav class="-mb-px flex gap-4" aria-label="Settings tabs">
				<button
					type="button"
					onclick={() => (activeTab = 'arm')}
					class="whitespace-nowrap border-b-2 px-1 py-2.5 text-sm font-medium transition-colors
						{activeTab === 'arm'
						? 'border-primary text-primary-text dark:border-primary-text-dark dark:text-primary-text-dark'
						: 'border-transparent text-gray-500 hover:border-primary/30 hover:text-gray-700 dark:text-gray-400 dark:hover:border-primary/30 dark:hover:text-gray-300'}"
				>
					ARM Standard Settings
				</button>
				<button
					type="button"
					onclick={() => (activeTab = 'transcoder')}
					class="whitespace-nowrap border-b-2 px-1 py-2.5 text-sm font-medium transition-colors
						{activeTab === 'transcoder'
						? 'border-primary text-primary-text dark:border-primary-text-dark dark:text-primary-text-dark'
						: 'border-transparent text-gray-500 hover:border-primary/30 hover:text-gray-700 dark:text-gray-400 dark:hover:border-primary/30 dark:hover:text-gray-300'}"
				>
					Dedicated Transcoder
				</button>
				<button
					type="button"
					onclick={() => (activeTab = 'appearance')}
					class="whitespace-nowrap border-b-2 px-1 py-2.5 text-sm font-medium transition-colors
						{activeTab === 'appearance'
						? 'border-primary text-primary-text dark:border-primary-text-dark dark:text-primary-text-dark'
						: 'border-transparent text-gray-500 hover:border-primary/30 hover:text-gray-700 dark:text-gray-400 dark:hover:border-primary/30 dark:hover:text-gray-300'}"
				>
					Appearance
				</button>
			</nav>
		</div>

		<!-- Transcoder Tab -->
		{#if activeTab === 'transcoder'}
			<div class="rounded-lg border border-primary/30 bg-primary-light-bg px-4 py-3 text-sm text-primary-dark dark:border-primary/30 dark:bg-primary-light-bg-dark/20 dark:text-primary-text-dark">
				These settings configure the <strong>dedicated transcoder container</strong>, a separate GPU-accelerated service that handles transcoding independently from ARM. Changes here do not affect ARM's built-in HandBrake/FFmpeg transcoding.
			</div>

			<!-- Cross-service awareness banner -->
			{#if skipTranscode}
				<div class="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm dark:border-green-800 dark:bg-green-900/20">
					<span class="inline-flex h-5 w-5 items-center justify-center rounded-full bg-green-100 text-xs font-bold text-green-700 dark:bg-green-900/40 dark:text-green-400">&#10003;</span>
					<span class="font-medium text-green-700 dark:text-green-400">Active</span>
					<span class="text-gray-600 dark:text-gray-400">&mdash; ARM's SKIP_TRANSCODE is enabled. Ripped media is ready for this transcoder.</span>
				</div>
			{:else}
				<div class="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm dark:border-amber-800 dark:bg-amber-900/20">
					<span class="inline-flex h-5 w-5 items-center justify-center rounded-full bg-amber-100 text-xs font-bold text-amber-700 dark:bg-amber-900/40 dark:text-amber-400">!</span>
					<span class="font-medium text-amber-700 dark:text-amber-400">ARM using built-in transcoding</span>
					<span class="text-gray-600 dark:text-gray-400">&mdash; Enable SKIP_TRANSCODE on the </span>
					<button type="button" onclick={() => { activeTab = 'arm'; window.scrollTo(0, 0); }} class="font-medium text-primary-text underline hover:text-primary-dark dark:text-primary-text-dark">ARM tab</button>
					<span class="text-gray-600 dark:text-gray-400"> to offload to this service.</span>
				</div>
			{/if}

			<!-- Service Status -->
			<section>
				<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Service Status</h2>
				<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
					<!-- Connection card -->
					<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-sm dark:border-primary/20 dark:bg-surface-dark">
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
					<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-sm dark:border-primary/20 dark:bg-surface-dark">
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
							<p class="mt-1 text-xs text-gray-400">Not saved &mdash; used only for this test.</p>
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
						<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-sm md:col-span-2 dark:border-primary/20 dark:bg-surface-dark">
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
							<p class="mt-3 text-xs text-gray-400">Authentication is configured via Docker environment variables (REQUIRE_API_AUTH, API_KEY, WEBHOOK_SECRET) on the transcoder container.</p>
						</div>
					{/if}
				</div>
			</section>

			<!-- Notification Script -->
			<section>
				<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Notification Script</h2>
				<div class="rounded-lg border border-primary/20 bg-surface p-4 shadow-sm dark:border-primary/20 dark:bg-surface-dark">
					<p class="mb-4 text-sm text-gray-600 dark:text-gray-400">
						Generates a script that ARM executes to notify the transcoder when a rip completes.
					</p>

					{#if scriptLoading}
						<p class="text-sm text-gray-400">Loading...</p>
					{:else}
						<div class="space-y-4">
							<!-- Transcoder Webhook URL -->
							<div>
								<label for="script-url" class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
									Transcoder Webhook URL
								</label>
								<input
									id="script-url"
									type="text"
									class={inputClass}
									placeholder="http://arm-transcoder:5000/webhook/arm"
									bind:value={scriptForm.transcoder_url}
								/>
								<p class="mt-1 text-xs text-gray-400">The full URL ARM uses to reach the transcoder webhook endpoint.</p>
							</div>

							<!-- Webhook Secret -->
							<div>
								<label for="script-secret" class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
									Webhook Secret
								</label>
								<input
									id="script-secret"
									type="password"
									class={inputClass}
									placeholder="Leave empty if webhook auth is disabled"
									bind:value={scriptForm.webhook_secret}
								/>
								<p class="mt-1 text-xs text-gray-400">Must match WEBHOOK_SECRET on the transcoder. Leave empty if webhook auth is disabled.</p>
							</div>

							<!-- Advanced toggle -->
							<div>
								<button
									type="button"
									onclick={() => (showAdvanced = !showAdvanced)}
									class="flex items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200"
								>
									<svg
										class="h-3.5 w-3.5 transform transition-transform {showAdvanced ? 'rotate-90' : ''}"
										fill="none" stroke="currentColor" viewBox="0 0 24 24"
									>
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
									</svg>
									Advanced
								</button>

								{#if showAdvanced}
									<div class="mt-3 space-y-4 rounded-md border border-primary/15 bg-page p-4 dark:border-primary/20 dark:bg-primary/5">
										<p class="text-xs text-gray-500 dark:text-gray-400">
											When both paths are set, the script moves ripped files from local scratch storage
											to a shared location before notifying the transcoder.
										</p>
										<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
											<div>
												<label for="script-local-raw" class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
													LOCAL_RAW_PATH
												</label>
												<input
													id="script-local-raw"
													type="text"
													class={inputClass}
													placeholder="e.g. /home/arm/media/raw"
													bind:value={scriptForm.local_raw_path}
												/>
												<p class="mt-1 text-xs text-gray-400">Local disk where ARM rips to.</p>
											</div>
											<div>
												<label for="script-shared-raw" class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
													SHARED_RAW_PATH
												</label>
												<input
													id="script-shared-raw"
													type="text"
													class={inputClass}
													placeholder="e.g. /mnt/media/raw"
													bind:value={scriptForm.shared_raw_path}
												/>
												<p class="mt-1 text-xs text-gray-400">Shared storage handoff directory.</p>
											</div>
										</div>
									</div>
								{/if}
							</div>

							<!-- Generate & Save button -->
							<div class="flex items-center gap-3">
								<button
									type="button"
									onclick={handleSaveScript}
									disabled={scriptSaving || !scriptForm.transcoder_url}
									class="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-on-primary hover:bg-primary-hover disabled:opacity-50 dark:bg-primary dark:hover:bg-primary-hover"
								>
									{scriptSaving ? 'Saving...' : 'Generate & Save'}
								</button>
								{#if scriptFeedback}
									<span class="text-sm {scriptFeedback.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
										{scriptFeedback.message}
									</span>
								{/if}
							</div>

							<!-- Script preview toggle -->
							{#if scriptInfo?.content}
								<div>
									<button
										type="button"
										onclick={() => (showScriptPreview = !showScriptPreview)}
										class="flex items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200"
									>
										<svg
											class="h-3.5 w-3.5 transform transition-transform {showScriptPreview ? 'rotate-90' : ''}"
											fill="none" stroke="currentColor" viewBox="0 0 24 24"
										>
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
										</svg>
										Preview Script
									</button>
									{#if showScriptPreview}
										<pre class="mt-2 max-h-80 overflow-auto rounded-md border border-primary/15 bg-page p-3 text-xs text-gray-700 dark:border-primary/20 dark:bg-primary/5 dark:text-gray-300">{scriptInfo.content}</pre>
									{/if}
								</div>
							{/if}
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
									<div class="rounded bg-primary/10 px-2 py-1 dark:bg-primary/15">
										<span class="font-medium text-gray-500 dark:text-gray-400">Raw:</span>
										<span class="ml-1 font-mono text-gray-700 dark:text-gray-200">{tcPaths.raw_path}</span>
									</div>
									<div class="rounded bg-primary/10 px-2 py-1 dark:bg-primary/15">
										<span class="font-medium text-gray-500 dark:text-gray-400">Completed:</span>
										<span class="ml-1 font-mono text-gray-700 dark:text-gray-200">{tcPaths.completed_path}</span>
									</div>
									<div class="rounded bg-primary/10 px-2 py-1 dark:bg-primary/15">
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
											class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out
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
															class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out
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

		<!-- ARM Tab -->
		{#if activeTab === 'arm'}
			{#if settings.arm_gpu_support}
				{@render gpuCards(settings.arm_gpu_support)}
			{/if}

			<section>
				<div class="mb-3 flex items-center justify-between gap-3">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Configuration</h2>
					<!-- Search input -->
					<div class="relative">
						<svg class="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
						</svg>
						<input
							type="text"
							placeholder="Filter settings..."
							class="w-56 rounded-md border border-primary/25 bg-primary/5 py-1.5 pl-8 pr-3 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white dark:placeholder-gray-500"
							bind:value={armSearch}
						/>
						{#if armSearch}
							<button
								type="button"
								onclick={() => (armSearch = '')}
								class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
							>
								<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
								</svg>
							</button>
						{/if}
					</div>
				</div>

				{#if settings.arm_config}
					{@const groups = getArmGroups(settings.arm_config)}
					{#if groups.length === 0 && armSearch}
						<p class="py-4 text-center text-sm text-gray-400">No settings match "{armSearch}"</p>
					{:else}
						<div class="space-y-2">
							{#each groups as group}
								<div
									class="rounded-lg border border-primary/20 bg-surface dark:border-primary/20 dark:bg-surface-dark"
								>
									<button
										type="button"
										onclick={() => toggleCollapse(group.label)}
										class="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold text-gray-900 hover:bg-page dark:text-white dark:hover:bg-primary/10"
									>
										<span>{group.label}</span>
										<svg
											class="h-4 w-4 transform transition-transform {armCollapsed[group.label]
												? ''
												: 'rotate-180'}"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M19 9l-7 7-7-7"
											/>
										</svg>
									</button>

									{#if !armCollapsed[group.label] || armSearch}
										<div class="border-t border-primary/20 px-4 py-3 dark:border-primary/20">
											{#if group.label === 'Transcoding' && skipTranscode}
												<div class="mb-4 rounded-lg border border-primary/20 bg-primary-light-bg px-4 py-3 text-sm dark:border-primary/30 dark:bg-primary-light-bg-dark/20">
													<span class="font-medium text-primary-dark dark:text-primary-text-dark">Transcoding is offloaded</span>
													<span class="text-gray-600 dark:text-gray-400"> &mdash; ARM's built-in transcoding is skipped. Configure the dedicated service on the </span>
													<button type="button" onclick={() => { activeTab = 'transcoder'; window.scrollTo(0, 0); }} class="font-medium text-primary-text underline hover:text-primary-dark dark:text-primary-text-dark dark:hover:text-primary-text-dark/80">Transcoder tab</button>.
												</div>
											{/if}
											<div class="space-y-4 {group.label === 'Transcoding' && skipTranscode ? 'opacity-50' : ''}">
												{#each group.subpanels as subpanel}
													{#if subpanel.label}
														<div class="space-y-4 rounded-md border border-primary/15 bg-page p-4 dark:border-primary/20 dark:bg-primary/5">
															<h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">{subpanel.label}</h3>
															{#if TRANSCODING_SECTIONS[subpanel.label]}
																{#each TRANSCODING_SECTIONS[subpanel.label] as section}
																	{@const sectionKeys = section.keys.filter(k => subpanel.keys.includes(k))}
																	{#if sectionKeys.length > 0}
																		<p class="text-xs font-medium uppercase tracking-wider text-gray-400 dark:text-gray-500">{section.label}</p>
																		<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
																			{#each sectionKeys as key}
																				{@render armField(key)}
																			{/each}
																		</div>
																	{/if}
																{/each}
															{:else}
																<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
																	{#each subpanel.keys as key}
																		{#if !isMetadataKeyHidden(key)}
																			{@render armField(key)}
																		{/if}
																	{/each}
																</div>
															{/if}
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
			</section>
		{/if}

		<!-- Appearance Tab -->
		{#if activeTab === 'appearance'}
			<section class="space-y-6">
				<!-- Color Scheme -->
				<div class="rounded-lg border border-primary/20 bg-surface p-6 shadow-sm dark:border-primary/20 dark:bg-surface-dark">
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
				<div class="rounded-lg border border-primary/20 bg-surface p-6 shadow-sm dark:border-primary/20 dark:bg-surface-dark">
					<div class="flex items-center justify-between">
						<div>
							<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Dark Mode</h2>
							<p class="text-sm text-gray-500 dark:text-gray-400">Toggle between light and dark mode.</p>
						</div>
						<div class="flex items-center gap-2">
							<button
								type="button"
								onclick={toggleTheme}
								class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out
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
					</div>
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
				<span class="h-2 w-2 flex-shrink-0 rounded-full bg-primary animate-pulse"></span>
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
