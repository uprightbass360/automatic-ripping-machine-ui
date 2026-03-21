import type { DashboardData } from '$lib/types/arm';
import { apiFetch } from './client';

export function fetchDashboard(): Promise<DashboardData> {
	return apiFetch<DashboardData>('/api/dashboard');
}

export function setRippingEnabled(enabled: boolean): Promise<unknown> {
	return apiFetch('/api/system/ripping-enabled', {
		method: 'POST',
		body: JSON.stringify({ enabled })
	});
}

export function checkMakemkvKey(): Promise<{ reachable: boolean; key_valid: boolean | null }> {
	return apiFetch('/api/dashboard/makemkv-key-check', {
		method: 'POST'
	});
}
