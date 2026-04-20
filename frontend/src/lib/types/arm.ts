import type { TranscoderJob } from './transcoder';

export interface Track {
	track_id: number;
	job_id: number;
	track_number: string | null;
	length: number | null;
	aspect_ratio: string | null;
	fps: number | null;
	enabled: boolean | null;
	basename: string | null;
	filename: string | null;
	orig_filename: string | null;
	new_filename: string | null;
	ripped: boolean | null;
	status: string | null;
	error: string | null;
	source: string | null;
	// Per-track title metadata (null = inherits from job)
	title: string | null;
	year: string | null;
	imdb_id: string | null;
	poster_url: string | null;
	video_type: string | null;
	// TVDB episode matching
	episode_number: string | null;
	episode_name: string | null;
	// User-specified output filename (overrides pattern rendering)
	custom_filename: string | null;
}

export interface Job {
	job_id: number;
	arm_version: string | null;
	crc_id: string | null;
	logfile: string | null;
	start_time: string | null;
	stop_time: string | null;
	job_length: string | null;
	status: string | null;
	stage: string | null;
	no_of_titles: number | null;
	title: string | null;
	title_auto: string | null;
	title_manual: string | null;
	year: string | null;
	year_auto: string | null;
	year_manual: string | null;
	video_type: string | null;
	video_type_auto: string | null;
	video_type_manual: string | null;
	imdb_id: string | null;
	imdb_id_auto: string | null;
	imdb_id_manual: string | null;
	poster_url: string | null;
	poster_url_auto: string | null;
	poster_url_manual: string | null;
	devpath: string | null;
	mountpoint: string | null;
	hasnicetitle: boolean | null;
	errors: string | null;
	disctype: string | null;
	label: string | null;
	path: string | null;
	raw_path: string | null;
	transcode_path: string | null;
	artist: string | null;
	artist_auto: string | null;
	artist_manual: string | null;
	album: string | null;
	album_auto: string | null;
	album_manual: string | null;
	season: string | null;
	season_auto: string | null;
	season_manual: string | null;
	episode: string | null;
	episode_auto: string | null;
	episode_manual: string | null;
	transcode_overrides: Record<string, unknown> | null;
	multi_title: boolean | null;
	title_pattern_override: string | null;
	folder_pattern_override: string | null;
	disc_number: number | null;
	disc_total: number | null;
	ejected: boolean | null;
	pid: number | null;
	manual_pause: boolean | null;
	source_type?: string;
	source_path?: string;
	wait_start_time: string | null;
	tracks_total: number | null;
	tracks_ripped: number | null;
	tvdb_id: number | null;
}

export interface JobDetail extends Job {
	tracks: Track[];
	config: Record<string, string | null> | null;
}

export interface JobListResponse {
	jobs: Job[];
	total: number;
	page: number;
	per_page: number;
	pages: number;
}

export interface SystemInfo {
	id: number;
	name: string | null;
	cpu: string | null;
	description: string | null;
	mem_total: number | null;
}

export interface HardwareInfo {
	cpu: string | null;
	memory_total_gb: number | null;
}

export interface Drive {
	drive_id: number;
	name: string | null;
	mount: string | null;
	job_id_current: number | null;
	job_id_previous: number | null;
	description: string | null;
	drive_mode: string | null;
	maker: string | null;
	model: string | null;
	serial: string | null;
	connection: string | null;
	read_cd: boolean | null;
	read_dvd: boolean | null;
	read_bd: boolean | null;
	firmware: string | null;
	location: string | null;
	stale: boolean | null;
	mdisc: number | null;
	serial_id: string | null;
	uhd_capable: boolean | null;
	rip_speed: number | null;
	prescan_cache_mb: number | null;
	prescan_timeout: number | null;
	prescan_retries: number | null;
	disc_enum_timeout: number | null;
	current_job: Job | null;
}

export interface Notification {
	id: number;
	title: string | null;
	message: string | null;
	trigger_time: string | null;
	seen: boolean;
	cleared: boolean;
}

export interface MemoryInfo {
	total_gb: number;
	used_gb: number;
	free_gb: number;
	percent: number;
}

export interface StoragePath {
	name: string;
	path: string;
	total_gb: number;
	used_gb: number;
	free_gb: number;
	percent: number;
}

export interface GpuSnapshot {
	vendor: string;
	utilization_percent: number | null;
	memory_used_mb: number | null;
	memory_total_mb: number | null;
	temperature_c: number | null;
	encoder_percent: number | null;
	power_draw_w: number | null;
	power_limit_w: number | null;
	clock_core_mhz: number | null;
	clock_memory_mhz: number | null;
}

export interface SystemStats {
	cpu_percent: number;
	cpu_temp: number;
	memory: MemoryInfo | null;
	storage: StoragePath[];
	gpu: GpuSnapshot | null;
}

export interface DashboardData {
	db_available: boolean;
	arm_online: boolean;
	active_jobs: Job[];
	system_info: HardwareInfo | null;
	drives_online: number;
	drive_names: Record<string, string>;
	notification_count: number;
	ripping_enabled: boolean;
	makemkv_key_valid: boolean | null;
	makemkv_key_checked_at: string | null;
	transcoder_online: boolean;
	transcoder_stats: Record<string, unknown> | null;
	transcoder_system_stats: SystemStats | null;
	active_transcodes: TranscoderJob[];
	system_stats: SystemStats | null;
	transcoder_info: HardwareInfo | null;
}

export interface LogFile {
	filename: string;
	size: number;
	modified: string;
}

export interface LogContent {
	filename: string;
	content: string;
	lines: number;
}

export interface LogEntry {
	timestamp: string;
	level: string;
	logger: string;
	event: string;
	job_id: number | null;
	label: string | null;
	raw: string;
}

export interface StructuredLogContent {
	filename: string;
	entries: LogEntry[];
	lines: number;
}

export interface SearchResult {
	title: string;
	year: string;
	imdb_id: string | null;
	media_type: string;
	poster_url: string | null;
}

export interface MediaDetail extends SearchResult {
	plot: string | null;
	background_url: string | null;
}

export interface MusicSearchResult {
	title: string;
	artist: string;
	year: string;
	release_id: string;
	media_type: string;
	poster_url: string | null;
	track_count: number | null;
	country: string | null;
	release_type: string | null;
	format: string | null;
	label: string | null;
}

export interface MusicDetail extends MusicSearchResult {
	catalog_number: string | null;
	barcode: string | null;
	status: string | null;
	disc_count: number | null;
	tracks: { number: string; title: string; length_ms: number | null; disc_number: number | null }[];
}

export interface TitleUpdate {
	title?: string;
	year?: string;
	video_type?: string;
	imdb_id?: string;
	poster_url?: string;
	path?: string;
	disctype?: string;
	label?: string;
	artist?: string;
	album?: string;
	season?: string;
	episode?: string;
}

export interface TrackTitleUpdate {
	title?: string;
	year?: string;
	video_type?: string;
	imdb_id?: string;
	poster_url?: string;
}

export interface JobConfigUpdate {
	RIPMETHOD?: 'mkv' | 'backup';
	DISCTYPE?: 'dvd' | 'bluray' | 'bluray4k' | 'music' | 'data';
	MAINFEATURE?: boolean;
	MINLENGTH?: number;
	MAXLENGTH?: number;
	AUDIO_FORMAT?: string;
	SKIP_TRANSCODE?: boolean;
}

export interface TranscoderConfig {
	config: Record<string, unknown>;
	updatable_keys: string[];
	paths?: { raw_path: string; completed_path: string; work_path: string };
	valid_video_encoders?: string[];
	valid_audio_encoders?: string[];
	valid_subtitle_modes?: string[];
	valid_log_levels?: string[];
	valid_handbrake_presets?: string[];
	valid_preset_files?: string[];
	presets_by_file?: Record<string, string[]>;
}

export interface TranscoderAuthStatus {
	require_api_auth: boolean;
	webhook_secret_configured: boolean;
}

export interface FolderScanResult {
	disc_type: string;
	label: string;
	title_suggestion: string;
	year_suggestion: string | null;
	folder_size_bytes: number;
	stream_count: number;
	disc_number?: number | null;
	disc_total?: number | null;
	season?: number | null;
}

export interface FolderCreateRequest {
	source_path: string;
	title: string;
	year?: string | null;
	video_type: string;
	disctype: string;
	imdb_id?: string | null;
	poster_url?: string | null;
	multi_title?: boolean;
	season?: number | null;
	disc_number?: number | null;
	disc_total?: number | null;
}

export interface FolderCreateResponse {
	job_id: number;
	status: string;
	source_type: string;
	source_path: string;
}

export interface SettingsData {
	arm_config: Record<string, string | null> | null;
	arm_metadata: Record<string, string> | null;
	arm_handbrake_presets: string[] | null;
	naming_variables: Record<string, string> | null;
	transcoder_config: TranscoderConfig | null;
	transcoder_gpu_support: Record<string, boolean> | null;
	transcoder_auth_status: TranscoderAuthStatus | null;
	/** @deprecated Use transcoder_gpu_support instead */
	gpu_support: Record<string, boolean> | null;
}
