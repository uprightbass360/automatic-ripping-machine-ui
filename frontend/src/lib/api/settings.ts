import type { SettingsData } from '$lib/types/arm';
import { apiFetch } from './client';

export function fetchSettings(): Promise<SettingsData> {
	return apiFetch<SettingsData>('/api/settings');
}

export function saveArmConfig(config: Record<string, string | null>): Promise<{ success: boolean; warning?: string }> {
	return apiFetch('/api/settings/arm', {
		method: 'PUT',
		body: JSON.stringify({ config })
	});
}

export function saveTranscoderConfig(config: Record<string, unknown>): Promise<{ success: boolean; applied?: Record<string, unknown> }> {
	return apiFetch('/api/settings/transcoder', {
		method: 'PATCH',
		body: JSON.stringify(config)
	});
}

export function testMetadataKey(): Promise<{ success: boolean; message: string; provider: string }> {
	return apiFetch('/api/settings/test-metadata');
}

export interface ConnectionTestResult {
	reachable: boolean;
	auth_ok: boolean;
	auth_required: boolean;
	gpu_support: Record<string, boolean> | null;
	worker_running: boolean;
	queue_size: number;
	error: string | null;
}

export interface WebhookTestResult {
	reachable: boolean;
	secret_ok: boolean;
	secret_required: boolean;
	error: string | null;
}

export function testTranscoderConnection(): Promise<ConnectionTestResult> {
	return apiFetch<ConnectionTestResult>('/api/settings/transcoder/test-connection', {
		method: 'POST'
	});
}

export function testTranscoderWebhook(secret: string): Promise<WebhookTestResult> {
	return apiFetch<WebhookTestResult>('/api/settings/transcoder/test-webhook', {
		method: 'POST',
		body: JSON.stringify({ webhook_secret: secret })
	});
}

export interface SystemInfoData {
	versions: Record<string, string>;
	endpoints: Record<string, { url: string; reachable: boolean }>;
	paths: Array<{
		setting: string;
		path: string;
		exists: boolean;
		writable: boolean;
	}>;
	database: {
		path: string;
		size_bytes: number | null;
		available: boolean;
	};
	drives: Array<{
		name: string | null;
		mount: string | null;
		maker: string | null;
		model: string | null;
		capabilities: string[];
		firmware: string | null;
	}>;
}

export function fetchSystemInfo(): Promise<SystemInfoData> {
	return apiFetch<SystemInfoData>('/api/settings/system-info');
}

export interface FailedJobSummary {
	job_id: number;
	status: string | null;
	title: string | null;
	label: string | null;
	raw_path: string | null;
	logfile: string | null;
	start_time: string | null;
}

export interface MaintenanceLogFile {
	path: string;
	relative_path: string;
	size: number;
}

export interface MaintenanceFolder {
	path: string;
	name: string;
	category: 'raw' | 'completed_movies';
}

export function fetchFailedJobs(): Promise<{ jobs: FailedJobSummary[] }> {
	return apiFetch<{ jobs: FailedJobSummary[] }>('/api/settings/maintenance/failed-jobs');
}

export function fetchMaintenanceLogFiles(): Promise<{ root: string; files: MaintenanceLogFile[] }> {
	return apiFetch('/api/settings/maintenance/log-files');
}

export function fetchMaintenanceFolders(): Promise<{ roots: { raw: string; completed_movies: string }; folders: MaintenanceFolder[] }> {
	return apiFetch('/api/settings/maintenance/folders');
}

export function maintenanceRescanDrives(): Promise<{ success?: boolean; drive_count?: number; drives_changed?: boolean; error?: string }> {
	return apiFetch('/api/settings/maintenance/rescan-drives', {
		method: 'POST'
	});
}

export function maintenanceClearJob(jobId: number): Promise<{ success: boolean; job_id: number; title?: string | null }> {
	return apiFetch('/api/settings/maintenance/clear-job', {
		method: 'POST',
		body: JSON.stringify({ job_id: jobId })
	});
}

export function maintenanceDeleteJobLogs(jobId: number): Promise<{ success: boolean; job_id: number; removed: string[]; missing: string[]; errors: string[] }> {
	return apiFetch('/api/settings/maintenance/delete-job-logs', {
		method: 'POST',
		body: JSON.stringify({ job_id: jobId })
	});
}

export function maintenanceDeleteJobRaw(jobId: number): Promise<{ success: boolean; job_id: number; removed: string[]; missing: string[]; errors: string[]; title?: string | null }> {
	return apiFetch('/api/settings/maintenance/delete-job-raw', {
		method: 'POST',
		body: JSON.stringify({ job_id: jobId })
	});
}

export function maintenancePurgeJob(jobId: number): Promise<{ success: boolean; job_id: number; errors: string[] }> {
	return apiFetch('/api/settings/maintenance/purge-job', {
		method: 'POST',
		body: JSON.stringify({ job_id: jobId })
	});
}

export function maintenanceDeleteLogPath(path: string): Promise<{ success: boolean; removed: string[]; missing: string[]; errors: string[] }> {
	return apiFetch('/api/settings/maintenance/delete-log-path', {
		method: 'POST',
		body: JSON.stringify({ path })
	});
}

export function maintenanceDeleteFolderPath(path: string): Promise<{ success: boolean; removed: string[]; missing: string[]; errors: string[] }> {
	return apiFetch('/api/settings/maintenance/delete-folder-path', {
		method: 'POST',
		body: JSON.stringify({ path })
	});
}
