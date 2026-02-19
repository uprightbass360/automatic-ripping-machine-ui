import type { TranscoderJob } from './transcoder';

export interface Track {
	track_id: number;
	job_id: number;
	track_number: string | null;
	length: number | null;
	aspect_ratio: string | null;
	fps: number | null;
	main_feature: boolean | null;
	basename: string | null;
	filename: string | null;
	orig_filename: string | null;
	new_filename: string | null;
	ripped: boolean | null;
	status: string | null;
	error: string | null;
	source: string | null;
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
	poster_url: string | null;
	devpath: string | null;
	mountpoint: string | null;
	hasnicetitle: boolean | null;
	errors: string | null;
	disctype: string | null;
	label: string | null;
	path: string | null;
	raw_path: string | null;
	transcode_path: string | null;
	ejected: boolean | null;
	pid: number | null;
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

export interface SystemStats {
	cpu_percent: number;
	cpu_temp: number;
	memory: MemoryInfo | null;
	storage: StoragePath[];
}

export interface DashboardData {
	db_available: boolean;
	active_jobs: Job[];
	system_info: HardwareInfo | null;
	drives_online: number;
	drive_names: Record<string, string>;
	notification_count: number;
	ripping_enabled: boolean;
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

export interface TitleUpdate {
	title?: string;
	year?: string;
	video_type?: string;
	imdb_id?: string;
	poster_url?: string;
	path?: string;
}

export interface JobConfigUpdate {
	RIPMETHOD?: 'mkv' | 'backup';
	DISCTYPE?: 'dvd' | 'bluray' | 'bluray4k' | 'music' | 'data';
	MAINFEATURE?: boolean;
	MINLENGTH?: number;
	MAXLENGTH?: number;
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

export interface SettingsData {
	arm_config: Record<string, string | null> | null;
	arm_metadata: Record<string, string> | null;
	arm_handbrake_presets: string[] | null;
	transcoder_config: TranscoderConfig | null;
	arm_gpu_support: Record<string, boolean> | null;
	transcoder_gpu_support: Record<string, boolean> | null;
	transcoder_auth_status: TranscoderAuthStatus | null;
	/** @deprecated Use transcoder_gpu_support instead */
	gpu_support: Record<string, boolean> | null;
}
