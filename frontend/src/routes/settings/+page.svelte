<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchSettings, saveArmConfig, saveTranscoderConfig } from '$lib/api/settings';
	import type { SettingsData } from '$lib/types/arm';

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
	let activeTab = $state<'arm' | 'transcoder'>('arm');

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
		const extraCustom = tcCustom.filter((n) => !seen.has(n));
		extraCustom.forEach((n) => seen.add(n));

		// Then built-in presets
		const extraBuiltin = builtin.filter((n) => !seen.has(n));

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
		const presetStd = filePresets.find((n) => !is4k(n) && !isDvd(n)) ?? filePresets[0];

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
		UNIDENTIFIED_EJECT: { label: 'Eject Unidentified Discs', description: 'Auto-eject discs that cannot be identified' },
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
		ARM_CHILDREN: { label: 'Child Servers', description: 'Comma-separated URLs of child ARM instances to show on the dashboard' },
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
			{ label: 'Post-Rip Behavior', keys: ['ALLOW_DUPLICATES', 'UNIDENTIFIED_EJECT', 'AUTO_EJECT', 'RIP_POSTER'] },
		]},
		{ label: 'Transcoding', subpanels: [
			{ label: 'General', keys: ['SKIP_TRANSCODE', 'DEST_EXT', 'USE_FFMPEG', 'MAX_CONCURRENT_TRANSCODES', 'DELRAWFILES'] },
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
			{ keys: ['ARM_NAME', 'ARM_CHILDREN', 'DISABLE_LOGIN', 'DATE_FORMAT', 'ARM_API_KEY'] },
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

	// HandBrake presets — loaded dynamically from the ARM container at startup.
	// Falls back to empty (renders as text input) if the init container hasn't run.
	let hbPresets = $derived(settings?.arm_handbrake_presets ?? []);

	// SELECT_OPTIONS is derived so it picks up dynamic HB presets
	let SELECT_OPTIONS = $derived<Record<string, string[]>>({
		VIDEOTYPE: ['auto', 'series', 'movie'],
		RIPMETHOD: ['mkv', 'backup', 'backup_dvd'],
		LOGLEVEL: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
		METADATA_PROVIDER: ['omdb', 'tmdb'],
		GET_AUDIO_TITLE: ['none', 'musicbrainz', 'freecddb'],
		...(hbPresets.length > 0
			? { HB_PRESET_DVD: hbPresets, HB_PRESET_BD: hbPresets }
			: {}),
	});

	function getArmGroups(config: Record<string, string | null>) {
		const allKeys = new Set(Object.keys(config));
		const mapped = new Set<string>();
		const groups: { label: string; subpanels: { label?: string; keys: string[] }[] }[] = [];

		for (const group of ARM_KEY_GROUPS) {
			const subpanels: { label?: string; keys: string[] }[] = [];
			for (const sp of group.subpanels) {
				const present = sp.keys.filter((k) => allKeys.has(k));
				present.forEach((k) => mapped.add(k));
				if (present.length > 0) {
					subpanels.push({ label: sp.label, keys: present });
				}
			}
			if (subpanels.length > 0) {
				groups.push({ label: group.label, subpanels });
			}
		}

		// Catch-all for any unmapped keys (future-proofing)
		const unmapped = [...allKeys].filter((k) => !mapped.has(k));
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
</script>

<svelte:head>
	<title>Settings - ARM UI</title>
</svelte:head>

<div class="space-y-6">
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
		<div class="border-b border-gray-200 dark:border-gray-700">
			<nav class="-mb-px flex gap-4" aria-label="Settings tabs">
				<button
					type="button"
					onclick={() => (activeTab = 'arm')}
					class="whitespace-nowrap border-b-2 px-1 py-2.5 text-sm font-medium transition-colors
						{activeTab === 'arm'
						? 'border-blue-500 text-blue-600 dark:border-blue-400 dark:text-blue-400'
						: 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:border-gray-600 dark:hover:text-gray-300'}"
				>
					ARM Standard Settings
				</button>
				<button
					type="button"
					onclick={() => (activeTab = 'transcoder')}
					class="whitespace-nowrap border-b-2 px-1 py-2.5 text-sm font-medium transition-colors
						{activeTab === 'transcoder'
						? 'border-blue-500 text-blue-600 dark:border-blue-400 dark:text-blue-400'
						: 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:border-gray-600 dark:hover:text-gray-300'}"
				>
					Dedicated Transcoder
				</button>
			</nav>
		</div>

		<!-- Transcoder Tab -->
		{#if activeTab === 'transcoder'}
			<div class="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800 dark:border-blue-800 dark:bg-blue-900/20 dark:text-blue-300">
				These settings configure the <strong>dedicated transcoder container</strong>, a separate GPU-accelerated service that handles transcoding independently from ARM. Changes here do not affect ARM's built-in HandBrake/FFmpeg transcoding.
			</div>

			{#if settings.transcoder_gpu_support}
				{@const gpu = settings.transcoder_gpu_support}
				<section>
					<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">
						Hardware Encoding
					</h2>
					<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
						{#each HW_GROUPS as group}
							{@const available = hasAny(gpu, group.keys)}
							<div
								class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800"
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
												class="inline-flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold {gpu[
													key
												]
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
			{/if}

			{#if settings.transcoder_config?.config}
				<section>
					<div class="mb-3 flex items-center justify-between">
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">
							Configuration
						</h2>
						<div class="flex items-center gap-3">
							{#if tcFeedback}
								<span
									class="text-sm {tcFeedback.type === 'success'
										? 'text-green-600 dark:text-green-400'
										: 'text-red-600 dark:text-red-400'}"
								>
									{tcFeedback.message}
								</span>
							{/if}
							<button
								onclick={handleTcSave}
								disabled={!tcDirty || tcSaving}
								class="rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-50
									{tcDirty
									? 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600'
									: 'bg-gray-400 dark:bg-gray-600'}"
							>
								{tcSaving ? 'Saving...' : 'Save'}
							</button>
						</div>
					</div>

					<div
						class="space-y-4 rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
					>
						<!-- Encoding sub-panel -->
						<div class="space-y-4 rounded-md border border-gray-100 bg-gray-50 p-4 dark:border-gray-600 dark:bg-gray-700/40">
							<h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Video Encoding</h3>

							<!-- Video Encoder -->
							<div>
								<label
									for="tc-video_encoder"
									class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
								>
									{TC_LABELS['video_encoder'] ?? 'Video Encoder'}
								</label>
								<select
									id="tc-video_encoder"
									class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
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

							<!-- Preset dropdowns (3-column row) -->
							<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
								{#each TC_PRESET_KEYS as key}
									{@const selectOpts = tcSelectOptions(key)}
									<div>
										<label
											for="tc-{key}"
											class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
										>
											{TC_LABELS[key] ?? key}
										</label>
										{#if selectOpts}
											<select
												id="tc-{key}"
												class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
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
												class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
												bind:value={tcForm[key]}
											/>
										{/if}
										{#if TC_HELP[key]}
											<p class="mt-1 text-xs text-gray-400">{TC_HELP[key]}</p>
										{/if}
									</div>
								{/each}
							</div>

							<!-- Custom Preset File (full width, last) -->
							{#if tcSelectOptions('handbrake_preset_file')}
								{@const pfOpts = tcSelectOptions('handbrake_preset_file')}
								<div>
									<label
										for="tc-handbrake_preset_file"
										class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
									>
										{TC_LABELS['handbrake_preset_file']}
									</label>
									<select
										id="tc-handbrake_preset_file"
										class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
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
							{/if}

							<!-- Audio & Subtitle streams (part of video transcode) -->
							<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
								{#each ['audio_encoder', 'subtitle_mode'] as key}
									{@const selectOpts = tcSelectOptions(key)}
									<div>
										<label
											for="tc-{key}"
											class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
										>
											{TC_LABELS[key] ?? key}
										</label>
										{#if selectOpts}
											<select
												id="tc-{key}"
												class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
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
												class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
												bind:value={tcForm[key]}
											/>
										{/if}
									</div>
								{/each}
							</div>
						</div>

						<!-- Directories sub-panel -->
						<div class="space-y-4 rounded-md border border-gray-100 bg-gray-50 p-4 dark:border-gray-600 dark:bg-gray-700/40">
							<h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Output Directories</h3>
							{#if tcPaths}
								<div class="grid grid-cols-1 gap-2 text-xs md:grid-cols-3">
									<div class="rounded bg-gray-100 px-2 py-1 dark:bg-gray-600/50">
										<span class="font-medium text-gray-500 dark:text-gray-400">Raw:</span>
										<span class="ml-1 font-mono text-gray-700 dark:text-gray-200">{tcPaths.raw_path}</span>
									</div>
									<div class="rounded bg-gray-100 px-2 py-1 dark:bg-gray-600/50">
										<span class="font-medium text-gray-500 dark:text-gray-400">Completed:</span>
										<span class="ml-1 font-mono text-gray-700 dark:text-gray-200">{tcPaths.completed_path}</span>
									</div>
									<div class="rounded bg-gray-100 px-2 py-1 dark:bg-gray-600/50">
										<span class="font-medium text-gray-500 dark:text-gray-400">Work:</span>
										<span class="ml-1 font-mono text-gray-700 dark:text-gray-200">{tcPaths.work_path}</span>
									</div>
								</div>
							{/if}
							<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
								{#each ['movies_subdir', 'tv_subdir', 'audio_subdir'] as key}
									<div>
										<label
											for="tc-{key}"
											class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
										>
											{TC_LABELS[key] ?? key}
										</label>
										<input
											id="tc-{key}"
											type="text"
											class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
											bind:value={tcForm[key]}
										/>
										{#if tcPaths}
											<p class="mt-1 text-xs font-mono text-gray-400">
												{tcPaths.completed_path}/{tcForm[key]}
											</p>
										{/if}
									</div>
								{/each}
							</div>
							<div>
								<label
									for="tc-delete_source"
									class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
								>
									{TC_LABELS['delete_source'] ?? 'Delete Source'}
								</label>
								<button
									type="button"
									onclick={() => (tcForm.delete_source = !tcForm.delete_source)}
									class="relative mt-1 inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out
										{tcForm.delete_source ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'}"
									role="switch"
									aria-checked={!!tcForm.delete_source}
									aria-label="Delete Source After Transcode"
								>
									<span
										class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out
											{tcForm.delete_source ? 'translate-x-5' : 'translate-x-0'}"
									></span>
								</button>
							</div>
						</div>

						<!-- Operational settings -->
						{#if settings.transcoder_config.updatable_keys.filter((k) => !TC_PRESET_SET.has(k)).length > 0}
							<div class="space-y-4 rounded-md border border-gray-100 bg-gray-50 p-4 dark:border-gray-600 dark:bg-gray-700/40">
								<h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">Operational</h3>
								<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
									{#each settings.transcoder_config.updatable_keys.filter((k) => !TC_PRESET_SET.has(k)) as key}
										{@const selectOpts = tcSelectOptions(key)}
										<div>
											<label
												for="tc-{key}"
												class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
											>
												{TC_LABELS[key] ?? key}
											</label>

											{#if selectOpts}
												<select
													id="tc-{key}"
													class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
													bind:value={tcForm[key]}
												>
													{#each selectOpts as opt}
														<option value={opt}>{opt}</option>
													{/each}
												</select>
											{:else if TC_BOOL_KEYS.has(key)}
												<button
													type="button"
													onclick={() => (tcForm[key] = !tcForm[key])}
													class="relative mt-1 inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out
														{tcForm[key] ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'}"
													role="switch"
													aria-checked={!!tcForm[key]}
													aria-label={TC_LABELS[key] ?? key}
												>
													<span
														class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out
															{tcForm[key] ? 'translate-x-5' : 'translate-x-0'}"
													></span>
												</button>
											{:else if TC_NUMBER_FIELDS[key]}
												{@const range = TC_NUMBER_FIELDS[key]}
												<input
													id="tc-{key}"
													type="number"
													min={range[0]}
													max={range[1]}
													step={range[2] ?? 1}
													class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
													bind:value={tcForm[key]}
												/>
											{:else}
												<input
													id="tc-{key}"
													type="text"
													class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
													bind:value={tcForm[key]}
												/>
											{/if}

											{#if TC_HELP[key]}
												<p class="mt-1 text-xs text-gray-400">{TC_HELP[key]}</p>
											{/if}
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
				{@const gpu = settings.arm_gpu_support}
				<section>
					<h2 class="mb-3 text-lg font-semibold text-gray-900 dark:text-white">
						Hardware Encoding
					</h2>
					<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
						{#each HW_GROUPS as group}
							{@const available = hasAny(gpu, group.keys)}
							<div
								class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800"
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
												class="inline-flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold {gpu[
													key
												]
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
			{/if}

			<section>
				<div class="mb-3 flex items-center justify-between">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Configuration</h2>
					<div class="flex items-center gap-3">
						{#if armFeedback}
							<span
								class="text-sm {armFeedback.type === 'success'
									? 'text-green-600 dark:text-green-400'
									: 'text-red-600 dark:text-red-400'}"
							>
								{armFeedback.message}
							</span>
						{/if}
						{#if settings.arm_config}
							<button
								onclick={handleArmSave}
								disabled={!armDirty || armSaving}
								class="rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-50
									{armDirty
									? 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600'
									: 'bg-gray-400 dark:bg-gray-600'}"
							>
								{armSaving ? 'Saving...' : 'Save'}
							</button>
						{/if}
					</div>
				</div>

				{#if settings.arm_config}
					{@const groups = getArmGroups(settings.arm_config)}
					<div class="space-y-2">
						{#each groups as group}
							<div
								class="rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800"
							>
								<button
									type="button"
									onclick={() => toggleCollapse(group.label)}
									class="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold text-gray-900 hover:bg-gray-50 dark:text-white dark:hover:bg-gray-700/50"
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

								{#if !armCollapsed[group.label]}
									<div class="border-t border-gray-200 px-4 py-3 dark:border-gray-700">
										<div class="space-y-4">
											{#each group.subpanels as subpanel}
												{#if subpanel.label}
													<div class="space-y-4 rounded-md border border-gray-100 bg-gray-50 p-4 dark:border-gray-600 dark:bg-gray-700/40">
														<h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">{subpanel.label}</h3>
														<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
															{#each subpanel.keys as key}
															{@const val = armForm[key] ?? ''}
															{@const comment = getComment(key)}
															<div>
																<div class="mb-1 flex items-center gap-1">
																	<label for="arm-{key}" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
																		{ARM_LABELS[key]?.label ?? key}
																	</label>
																	<button
																		type="button"
																		onclick={() => toggleInfo(key)}
																		class="inline-flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold
																			{armInfoKeys.has(key)
																			? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400'
																			: 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'}
																			hover:bg-blue-200 dark:hover:bg-blue-800/40"
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
																		class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
																		value={curVal}
																		onchange={(e) =>
																			(armForm[key] = (
																				e.target as HTMLSelectElement
																			).value)}
																	>
																		{#if curVal && !opts.includes(curVal)}
																			<option value={curVal}>{curVal}</option>
																		{/if}
																		{#each opts as opt}
																			<option value={opt}>{opt}</option>
																		{/each}
																	</select>
																{:else if isBoolStr(val?.toString())}
																	<button
																		type="button"
																		onclick={() => toggleBool(key)}
																		class="relative mt-1 inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out
																			{val?.toString().toLowerCase() === 'true'
																			? 'bg-blue-600'
																			: 'bg-gray-300 dark:bg-gray-600'}"
																		role="switch"
																		aria-checked={val?.toString().toLowerCase() ===
																			'true'}
																		aria-label={key}
																	>
																		<span
																			class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out
																				{val?.toString().toLowerCase() === 'true'
																				? 'translate-x-5'
																				: 'translate-x-0'}"
																		></span>
																	</button>
																{:else if HIDDEN_KEYS.has(key)}
																	<div class="flex gap-1">
																		<input
																			id="arm-{key}"
																			type={armRevealedKeys.has(key)
																				? 'text'
																				: 'password'}
																			class="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
																			value={val?.toString() ?? ''}
																			oninput={(e) =>
																				(armForm[key] = (
																					e.target as HTMLInputElement
																				).value)}
																		/>
																		<button
																			type="button"
																			onclick={() => toggleReveal(key)}
																			class="rounded-md border border-gray-300 px-2 py-2 text-xs text-gray-600 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700"
																		>
																			{armRevealedKeys.has(key) ? 'Hide' : 'Show'}
																		</button>
																	</div>
																{:else if isIntStr(val?.toString())}
																	<input
																		id="arm-{key}"
																		type="number"
																		class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
																		value={val?.toString() ?? ''}
																		oninput={(e) =>
																			(armForm[key] = (
																				e.target as HTMLInputElement
																			).value)}
																	/>
																{:else}
																	<input
																		id="arm-{key}"
																		type="text"
																		class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
																		value={val?.toString() ?? ''}
																		oninput={(e) =>
																			(armForm[key] = (
																				e.target as HTMLInputElement
																			).value)}
																	/>
																{/if}
															
																{#if ARM_LABELS[key]?.description}
																	<p class="mt-1 text-xs text-gray-400">{ARM_LABELS[key].description}</p>
																{:else if comment}
																	<p class="mt-1 text-xs text-gray-400">{comment}</p>
																{/if}
															</div>
															{/each}
														</div>
													</div>
												{:else}
													<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
														{#each subpanel.keys as key}
														{@const val = armForm[key] ?? ''}
														{@const comment = getComment(key)}
														<div>
															<div class="mb-1 flex items-center gap-1">
																<label for="arm-{key}" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
																	{ARM_LABELS[key]?.label ?? key}
																</label>
																<button
																	type="button"
																	onclick={() => toggleInfo(key)}
																	class="inline-flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold
																		{armInfoKeys.has(key)
																		? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400'
																		: 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'}
																		hover:bg-blue-200 dark:hover:bg-blue-800/40"
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
																	class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
																	value={curVal}
																	onchange={(e) =>
																		(armForm[key] = (
																			e.target as HTMLSelectElement
																		).value)}
																>
																	{#if curVal && !opts.includes(curVal)}
																		<option value={curVal}>{curVal}</option>
																	{/if}
																	{#each opts as opt}
																		<option value={opt}>{opt}</option>
																	{/each}
																</select>
															{:else if isBoolStr(val?.toString())}
																<button
																	type="button"
																	onclick={() => toggleBool(key)}
																	class="relative mt-1 inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out
																		{val?.toString().toLowerCase() === 'true'
																		? 'bg-blue-600'
																		: 'bg-gray-300 dark:bg-gray-600'}"
																	role="switch"
																	aria-checked={val?.toString().toLowerCase() ===
																		'true'}
																	aria-label={key}
																>
																	<span
																		class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out
																			{val?.toString().toLowerCase() === 'true'
																			? 'translate-x-5'
																			: 'translate-x-0'}"
																	></span>
																</button>
															{:else if HIDDEN_KEYS.has(key)}
																<div class="flex gap-1">
																	<input
																		id="arm-{key}"
																		type={armRevealedKeys.has(key)
																			? 'text'
																			: 'password'}
																		class="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
																		value={val?.toString() ?? ''}
																		oninput={(e) =>
																			(armForm[key] = (
																				e.target as HTMLInputElement
																			).value)}
																	/>
																	<button
																		type="button"
																		onclick={() => toggleReveal(key)}
																		class="rounded-md border border-gray-300 px-2 py-2 text-xs text-gray-600 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700"
																	>
																		{armRevealedKeys.has(key) ? 'Hide' : 'Show'}
																	</button>
																</div>
															{:else if isIntStr(val?.toString())}
																<input
																	id="arm-{key}"
																	type="number"
																	class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
																	value={val?.toString() ?? ''}
																	oninput={(e) =>
																		(armForm[key] = (
																			e.target as HTMLInputElement
																		).value)}
																/>
															{:else}
																<input
																	id="arm-{key}"
																	type="text"
																	class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
																	value={val?.toString() ?? ''}
																	oninput={(e) =>
																		(armForm[key] = (
																			e.target as HTMLInputElement
																		).value)}
																/>
															{/if}
														
															{#if ARM_LABELS[key]?.description}
																<p class="mt-1 text-xs text-gray-400">{ARM_LABELS[key].description}</p>
															{:else if comment}
																<p class="mt-1 text-xs text-gray-400">{comment}</p>
															{/if}
														</div>
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
				{:else}
					<p class="text-sm text-gray-400">No ARM configuration found.</p>
				{/if}
			</section>
		{/if}
	{/if}
</div>
