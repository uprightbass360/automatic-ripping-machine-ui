export interface TranscoderJob {
	id: number;
	title: string;
	source_path: string;
	status: string;
	progress: number;
	error: string | null;
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
	[key: string]: unknown;
}

export interface TranscoderStats {
	online: boolean;
	stats: TranscoderStatsData | null;
}
