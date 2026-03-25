import { apiFetch } from './client';

export interface MaintenanceSummary {
	orphan_logs: number | null;
	orphan_folders: number | null;
	unseen_notifications: number | null;
	cleared_notifications: number | null;
	stale_transcoder_jobs: number | null;
}

export interface OrphanLog {
	path: string;
	relative_path: string;
	size_bytes: number;
}

export interface OrphanFolder {
	path: string;
	name: string;
	category: 'raw' | 'completed';
	size_bytes: number;
}

export interface OrphanLogsResponse {
	root: string;
	total_size_bytes: number;
	files: OrphanLog[];
}

export interface OrphanFoldersResponse {
	total_size_bytes: number;
	folders: OrphanFolder[];
}

export interface BulkDeleteResult {
	removed: string[];
	errors: string[];
}

export function fetchSummary(): Promise<MaintenanceSummary> {
	return apiFetch('/api/maintenance/summary');
}

export function fetchOrphanLogs(): Promise<OrphanLogsResponse> {
	return apiFetch('/api/maintenance/orphan-logs');
}

export function fetchOrphanFolders(): Promise<OrphanFoldersResponse> {
	return apiFetch('/api/maintenance/orphan-folders');
}

export function deleteLog(path: string): Promise<{ success: boolean }> {
	return apiFetch('/api/maintenance/delete-log', { method: 'POST', body: JSON.stringify({ path }) });
}

export function deleteFolder(path: string): Promise<{ success: boolean }> {
	return apiFetch('/api/maintenance/delete-folder', { method: 'POST', body: JSON.stringify({ path }) });
}

export function bulkDeleteLogs(paths: string[]): Promise<BulkDeleteResult> {
	return apiFetch('/api/maintenance/bulk-delete-logs', { method: 'POST', body: JSON.stringify({ paths }) });
}

export function bulkDeleteFolders(paths: string[]): Promise<BulkDeleteResult> {
	return apiFetch('/api/maintenance/bulk-delete-folders', { method: 'POST', body: JSON.stringify({ paths }) });
}

export function dismissAllNotifications(): Promise<{ success: boolean; count: number }> {
	return apiFetch('/api/maintenance/dismiss-all-notifications', { method: 'POST' });
}

export function purgeNotifications(): Promise<{ success: boolean; count: number }> {
	return apiFetch('/api/maintenance/purge-notifications', { method: 'POST' });
}

export function cleanupTranscoder(): Promise<{ success: boolean; deleted: number; errors: string[] }> {
	return apiFetch('/api/maintenance/cleanup-transcoder', { method: 'POST' });
}

export interface ImageCacheStats {
	count: number;
	size_bytes: number;
	size_mb: number;
	oldest: number | null;
	path: string;
}

export function fetchImageCacheStats(): Promise<ImageCacheStats> {
	return apiFetch('/api/maintenance/image-cache-stats');
}

export function clearImageCache(): Promise<{ success: boolean; cleared: number; freed_bytes: number }> {
	return apiFetch('/api/maintenance/clear-image-cache', { method: 'POST' });
}

export interface ClearRawResult {
	success: boolean;
	cleared: number;
	freed_bytes: number;
	errors: string[];
	path: string;
}

export function clearRaw(): Promise<ClearRawResult> {
	return apiFetch('/api/maintenance/clear-raw', { method: 'POST' });
}
