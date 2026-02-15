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
