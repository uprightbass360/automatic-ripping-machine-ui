import type { DashboardData } from '$lib/types/arm';
import { apiFetch } from './client';

export function fetchDashboard(): Promise<DashboardData> {
	return apiFetch<DashboardData>('/api/dashboard');
}
