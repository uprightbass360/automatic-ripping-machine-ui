import { apiFetch } from './client';

export interface JobStats {
	by_status: Record<string, number>;
	by_type: Record<string, number>;
	total: number;
}

export function fetchJobStats(): Promise<JobStats> {
	return apiFetch<JobStats>('/api/system/job-stats');
}

export function restartArm(): Promise<{ success: boolean }> {
	return apiFetch('/api/system/restart', { method: 'POST' });
}
