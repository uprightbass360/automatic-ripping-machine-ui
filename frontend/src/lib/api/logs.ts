import type { LogContent, LogFile, StructuredLogContent } from '$lib/types/arm';
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

export function fetchStructuredLogContent(
	filename: string,
	mode: 'tail' | 'full' = 'tail',
	lines: number = 100,
	level?: string,
	search?: string
): Promise<StructuredLogContent> {
	const params = new URLSearchParams({ mode, lines: String(lines) });
	if (level) params.set('level', level);
	if (search) params.set('search', search);
	return apiFetch<StructuredLogContent>(
		`/api/logs/${encodeURIComponent(filename)}/structured?${params}`
	);
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

export function fetchStructuredTranscoderLogContent(
	filename: string,
	mode: 'tail' | 'full' = 'tail',
	lines: number = 100,
	level?: string,
	search?: string
): Promise<StructuredLogContent> {
	const params = new URLSearchParams({ mode, lines: String(lines) });
	if (level) params.set('level', level);
	if (search) params.set('search', search);
	return apiFetch<StructuredLogContent>(
		`/api/transcoder/logs/${encodeURIComponent(filename)}/structured?${params}`
	);
}
