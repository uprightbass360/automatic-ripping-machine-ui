import { createPollingStore } from './polling';
import { fetchDashboard } from '$lib/api/dashboard';
import type { DashboardData } from '$lib/types/arm';

const emptyDashboard: DashboardData = {
	db_available: true,
	active_jobs: [],
	system_info: null,
	drives_online: 0,
	notification_count: 0,
	transcoder_online: false,
	transcoder_stats: null,
	active_transcodes: []
};

/** Singleton dashboard store — survives page navigations, retains last-known data. */
export const dashboard = createPollingStore(fetchDashboard, emptyDashboard, 5000);
