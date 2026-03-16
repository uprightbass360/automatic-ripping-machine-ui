import { apiFetch } from './client';

export interface ThemeMeta {
	id: string;
	label: string;
	version?: number;
	author?: string;
	description?: string;
	swatch: string;
	mode?: 'light' | 'dark';
	builtin?: boolean;
	tokens: Record<string, string>;
}

export interface ThemeFull extends ThemeMeta {
	css: string;
}

export function fetchThemes(): Promise<ThemeMeta[]> {
	return apiFetch<ThemeMeta[]>('/api/themes');
}

export function fetchTheme(id: string): Promise<ThemeFull> {
	return apiFetch<ThemeFull>(`/api/themes/${encodeURIComponent(id)}`);
}

export function uploadTheme(theme: ThemeFull): Promise<ThemeFull> {
	return apiFetch<ThemeFull>('/api/themes', {
		method: 'POST',
		body: JSON.stringify(theme)
	});
}

export function deleteTheme(id: string): Promise<void> {
	return apiFetch<void>(`/api/themes/${encodeURIComponent(id)}`, {
		method: 'DELETE'
	});
}
