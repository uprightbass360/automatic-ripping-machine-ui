import type { JobDetail, JobListResponse } from '$lib/types/arm';
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

export function deleteJob(id: number): Promise<unknown> {
	return apiFetch(`/api/jobs/${id}`, { method: 'DELETE' });
}

export function fixJobPermissions(id: number): Promise<unknown> {
	return apiFetch(`/api/jobs/${id}/fix-permissions`, { method: 'POST' });
}
