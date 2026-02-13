import type { LogContent, LogFile } from '$lib/types/arm';
import { apiFetch } from './client';

export function fetchLogs(): Promise<LogFile[]> {
	return apiFetch<LogFile[]>('/api/logs');
}

export function fetchLogContent(
	filename: string,
	mode: 'tail' | 'full' = 'tail',
	lines: number = 100
): Promise<LogContent> {
	return apiFetch<LogContent>(`/api/logs/${encodeURIComponent(filename)}?mode=${mode}&lines=${lines}`);
}

export function fetchTranscoderLogs(): Promise<LogFile[]> {
	return apiFetch<LogFile[]>('/api/transcoder/logs');
}

export function fetchTranscoderLogContent(
	filename: string,
	mode: 'tail' | 'full' = 'tail',
	lines: number = 100
): Promise<LogContent> {
	return apiFetch<LogContent>(
		`/api/transcoder/logs/${encodeURIComponent(filename)}?mode=${mode}&lines=${lines}`
	);
}
