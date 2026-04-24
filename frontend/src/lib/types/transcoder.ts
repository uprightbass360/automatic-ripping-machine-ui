export interface TranscoderJob {
	id: number;
	title: string;
	source_path: string;
	status: string;
	progress: number;
	current_fps: number | null;
	error: string | null;
	logfile: string | null;
	video_type: string | null;
	year: string | null;
	disctype: string | null;
	arm_job_id: string | null;
	output_path: string | null;
	total_tracks: number | null;
	poster_url: string | null;
	config_overrides: Record<string, unknown> | null;
	created_at: string | null;
	started_at: string | null;
	completed_at: string | null;
	[key: string]: unknown;
}

export interface TranscoderJobListResponse {
	jobs: TranscoderJob[];
	total: number;
}

export interface TranscoderStatsData {
	pending: number;
	processing: number;
	completed: number;
	failed: number;
	cancelled: number;
	worker_running: boolean;
	current_job: string | null;
	active_count: number;
	max_concurrent: number;
	[key: string]: unknown;
}

export interface TranscoderStats {
	online: boolean;
	stats: TranscoderStatsData | null;
}

export interface WorkerStatus {
	worker_id: number;
	status: 'idle' | 'processing';
	current_job: string | null;
	current_job_id: number | null;
	started_at: string | null;
}

export interface WorkersResponse {
	max_concurrent: number;
	active_count: number;
	workers: WorkerStatus[];
}
