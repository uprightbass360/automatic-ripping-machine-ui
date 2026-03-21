import { apiFetch } from './client';
import type { FolderScanResult, FolderCreateRequest, FolderCreateResponse } from '../types/arm';
import type { DirectoryListing, FileRoot } from '../types/files';

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

export function fetchIngressDirectory(path: string): Promise<DirectoryListing> {
	return apiFetch(`/api/files/list?path=${encodeURIComponent(path)}`);
}

export function fetchIngressRoot(): Promise<FileRoot[]> {
	return apiFetch('/api/files/roots');
}
