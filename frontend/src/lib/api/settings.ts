import type { SettingsData } from '$lib/types/arm';
import { apiFetch } from './client';

export function fetchSettings(): Promise<SettingsData> {
	return apiFetch<SettingsData>('/api/settings');
}

export function saveArmConfig(config: Record<string, string | null>): Promise<{ success: boolean; warning?: string }> {
	return apiFetch('/api/settings/arm', {
		method: 'PUT',
		body: JSON.stringify({ config })
	});
}

export function saveTranscoderConfig(config: Record<string, unknown>): Promise<{ success: boolean; applied?: Record<string, unknown> }> {
	return apiFetch('/api/settings/transcoder', {
		method: 'PATCH',
		body: JSON.stringify(config)
	});
}
