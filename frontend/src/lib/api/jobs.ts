import type { JobConfigUpdate, JobDetail, JobListResponse, MediaDetail, MusicDetail, MusicSearchResult, SearchResult, TitleUpdate } from '$lib/types/arm';
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

export function pauseWaitingJob(id: number): Promise<unknown> {
	return apiFetch(`/api/jobs/${id}/pause`, { method: 'POST' });
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

export interface MusicSearchResponse {
	results: MusicSearchResult[];
	total: number;
}

export function searchMusicMetadata(
	query: string,
	filters?: { artist?: string; release_type?: string; format?: string; country?: string; status?: string; tracks?: number },
	offset = 0
): Promise<MusicSearchResponse> {
	const params = new URLSearchParams({ q: query });
	if (filters?.artist) params.set('artist', filters.artist);
	if (filters?.release_type) params.set('release_type', filters.release_type);
	if (filters?.format) params.set('format', filters.format);
	if (filters?.country) params.set('country', filters.country);
	if (filters?.status) params.set('status', filters.status);
	if (filters?.tracks) params.set('tracks', String(filters.tracks));
	if (offset > 0) params.set('offset', String(offset));
	return apiFetch<MusicSearchResponse>(`/api/metadata/music/search?${params}`);
}

export function fetchMusicDetail(releaseId: string): Promise<MusicDetail> {
	return apiFetch<MusicDetail>(`/api/metadata/music/${releaseId}`);
}

export function setJobTracks(
	jobId: number,
	tracks: { track_number: string; title: string; length_ms: number | null }[]
): Promise<unknown> {
	return apiFetch(`/api/jobs/${jobId}/tracks`, {
		method: 'PUT',
		body: JSON.stringify(tracks)
	});
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

export interface CrcLookupResult {
	title: string;
	year: string;
	imdb_id: string;
	tmdb_id: string;
	video_type: string;
	disctype: string;
	label: string;
	poster_url: string;
	hasnicetitle: string;
	validated: string;
	date_added: string;
}

export interface CrcLookupResponse {
	found: boolean;
	results: CrcLookupResult[];
	no_crc?: boolean;
	error?: string;
	has_api_key?: boolean;
}

export function fetchCrcLookup(jobId: number): Promise<CrcLookupResponse> {
	return apiFetch<CrcLookupResponse>(`/api/jobs/${jobId}/crc-lookup`);
}

export function submitToCrcDb(id: number): Promise<unknown> {
	return apiFetch(`/api/jobs/${id}/crc-submit`, { method: 'POST' });
}

export interface RipProgress {
	progress: number | null;
	stage: string | null;
	tracks_total: number;
	tracks_ripped: number;
}

export function fetchJobProgress(id: number): Promise<RipProgress> {
	return apiFetch<RipProgress>(`/api/jobs/${id}/progress`);
}

export function retranscodeJob(id: number): Promise<{ status: string; message: string }> {
	return apiFetch(`/api/jobs/${id}/retranscode`, { method: 'POST' });
}
