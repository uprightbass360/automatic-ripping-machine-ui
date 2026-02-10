import type { TranscoderJobListResponse, TranscoderStats } from '$lib/types/transcoder';
import { apiFetch } from './client';

export function fetchTranscoderStats(): Promise<TranscoderStats> {
	return apiFetch<TranscoderStats>('/api/transcoder/stats');
}

export function fetchTranscoderJobs(params?: {
	status?: string;
	limit?: number;
	offset?: number;
}): Promise<TranscoderJobListResponse> {
	const query = new URLSearchParams();
	if (params?.status) query.set('status', params.status);
	if (params?.limit) query.set('limit', String(params.limit));
	if (params?.offset) query.set('offset', String(params.offset));
	const qs = query.toString();
	return apiFetch<TranscoderJobListResponse>(`/api/transcoder/jobs${qs ? `?${qs}` : ''}`);
}

export function retryTranscoderJob(id: number): Promise<unknown> {
	return apiFetch(`/api/transcoder/jobs/${id}/retry`, { method: 'POST' });
}

export function deleteTranscoderJob(id: number): Promise<unknown> {
	return apiFetch(`/api/transcoder/jobs/${id}`, { method: 'DELETE' });
}
