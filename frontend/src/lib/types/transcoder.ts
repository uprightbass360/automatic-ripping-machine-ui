export interface TranscoderJob {
	id: number;
	input_path: string;
	output_path: string;
	status: string;
	progress: number;
	preset: string | null;
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
	current_job: number | null;
	[key: string]: unknown;
}

export interface TranscoderStats {
	online: boolean;
	stats: TranscoderStatsData | null;
}
