import { apiFetch } from './client';
import type { FolderScanResult, FolderCreateRequest, FolderCreateResponse, DirectoryListing, FileRoot } from '../types/api.gen';

// TODO: replace with codegen types from $lib/types/api.gen once arm-neu PR #333
// (ISO import endpoints) is merged and the BFF exposes /api/jobs/iso/*. Until
// then, these mirror the spec response shape at
// docs/superpowers/specs/2026-05-04-iso-import-design.md.
export interface IsoScanResult {
	disc_type: string;
	label: string;
	title_suggestion: string | null;
	year_suggestion: string | null;
	iso_size: number;
	stream_count: number;
	volume_id: string | null;
	success?: boolean;
}

export interface IsoCreateRequest {
	source_path: string;
	title: string;
	year?: string | null;
	video_type: string;
	disctype: string;
	imdb_id?: string | null;
	poster_url?: string | null;
	multi_title?: boolean;
	season?: number | null;
	disc_number?: number | null;
	disc_total?: number | null;
}

export interface IsoCreateResponse {
	success: boolean;
	job_id: number;
}

export function scanFolder(path: string): Promise<FolderScanResult> {
	return apiFetch('/api/jobs/folder/scan', {
		method: 'POST',
		body: JSON.stringify({ path })
	});
}

export function createFolderJob(data: FolderCreateRequest): Promise<FolderCreateResponse> {
	return apiFetch('/api/jobs/folder', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export function scanIso(path: string): Promise<IsoScanResult> {
	return apiFetch('/api/jobs/iso/scan', {
		method: 'POST',
		body: JSON.stringify({ path })
	});
}

export function createIsoJob(data: IsoCreateRequest): Promise<IsoCreateResponse> {
	return apiFetch('/api/jobs/iso', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export function fetchIngressDirectory(path: string): Promise<DirectoryListing> {
	return apiFetch(`/api/files/list?path=${encodeURIComponent(path)}`);
}

export function fetchIngressRoot(): Promise<FileRoot[]> {
	return apiFetch('/api/files/roots');
}
