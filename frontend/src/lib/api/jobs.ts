import type { JobConfigUpdate, JobDetail, JobListResponse, MediaDetail, SearchResult, TitleUpdate } from '$lib/types/arm';
import { apiFetch } from './client';

export function fetchJobs(params?: {
	page?: number;
	per_page?: number;
	status?: string;
	search?: string;
	video_type?: string;
}): Promise<JobListResponse> {
	const query = new URLSearchParams();
	if (params?.page) query.set('page', String(params.page));
	if (params?.per_page) query.set('per_page', String(params.per_page));
	if (params?.status) query.set('status', params.status);
	if (params?.search) query.set('search', params.search);
	if (params?.video_type) query.set('video_type', params.video_type);
	const qs = query.toString();
	return apiFetch<JobListResponse>(`/api/jobs${qs ? `?${qs}` : ''}`);
}

export function fetchJob(id: number): Promise<JobDetail> {
	return apiFetch<JobDetail>(`/api/jobs/${id}`);
}

export function abandonJob(id: number): Promise<unknown> {
	return apiFetch(`/api/jobs/${id}/abandon`, { method: 'POST' });
}

export function cancelWaitingJob(id: number): Promise<unknown> {
	return apiFetch(`/api/jobs/${id}/cancel`, { method: 'POST' });
}

export function startWaitingJob(id: number): Promise<unknown> {
	return apiFetch(`/api/jobs/${id}/start`, { method: 'POST' });
}

export function deleteJob(id: number): Promise<unknown> {
	return apiFetch(`/api/jobs/${id}`, { method: 'DELETE' });
}

export function fixJobPermissions(id: number): Promise<unknown> {
	return apiFetch(`/api/jobs/${id}/fix-permissions`, { method: 'POST' });
}

export function searchMetadata(query: string, year?: string): Promise<SearchResult[]> {
	const params = new URLSearchParams({ q: query });
	if (year) params.set('year', year);
	return apiFetch<SearchResult[]>(`/api/metadata/search?${params}`);
}

export function fetchMediaDetail(imdbId: string): Promise<MediaDetail> {
	return apiFetch<MediaDetail>(`/api/metadata/${imdbId}`);
}

export function updateJobTitle(jobId: number, data: Partial<TitleUpdate>): Promise<unknown> {
	return apiFetch(`/api/jobs/${jobId}/title`, {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

export function updateJobConfig(jobId: number, data: Partial<JobConfigUpdate>): Promise<unknown> {
	return apiFetch(`/api/jobs/${jobId}/config`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

export interface RipProgress {
	progress: number | null;
	stage: string | null;
}

export function fetchJobProgress(id: number): Promise<RipProgress> {
	return apiFetch<RipProgress>(`/api/jobs/${id}/progress`);
}

export function retranscodeJob(id: number): Promise<{ status: string; message: string }> {
	return apiFetch(`/api/jobs/${id}/retranscode`, { method: 'POST' });
}
