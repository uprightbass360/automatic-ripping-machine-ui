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

export function testMetadataKey(): Promise<{ success: boolean; message: string; provider: string }> {
	return apiFetch('/api/settings/test-metadata');
}

export interface ConnectionTestResult {
	reachable: boolean;
	auth_ok: boolean;
	auth_required: boolean;
	gpu_support: Record<string, boolean> | null;
	worker_running: boolean;
	queue_size: number;
	error: string | null;
}

export interface WebhookTestResult {
	reachable: boolean;
	secret_ok: boolean;
	secret_required: boolean;
	error: string | null;
}

export function testTranscoderConnection(): Promise<ConnectionTestResult> {
	return apiFetch<ConnectionTestResult>('/api/settings/transcoder/test-connection', {
		method: 'POST'
	});
}

export function testTranscoderWebhook(secret: string): Promise<WebhookTestResult> {
	return apiFetch<WebhookTestResult>('/api/settings/transcoder/test-webhook', {
		method: 'POST',
		body: JSON.stringify({ webhook_secret: secret })
	});
}

export interface SystemInfoData {
	versions: Record<string, string>;
	paths: Array<{
		setting: string;
		path: string;
		exists: boolean;
		writable: boolean;
	}>;
	database: {
		path: string;
		size_bytes: number | null;
		available: boolean;
	};
	drives: Array<{
		name: string | null;
		mount: string | null;
		maker: string | null;
		model: string | null;
		capabilities: string[];
		firmware: string | null;
	}>;
}

export function fetchSystemInfo(): Promise<SystemInfoData> {
	return apiFetch<SystemInfoData>('/api/settings/system-info');
}
