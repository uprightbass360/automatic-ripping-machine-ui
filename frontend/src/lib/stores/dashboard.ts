import { createPollingStore } from './polling';
import { fetchDashboard } from '$lib/api/dashboard';
import type { DashboardData } from '$lib/types/arm';

const emptyDashboard: DashboardData = {
	db_available: true,
	active_jobs: [],
	system_info: null,
	drives_online: 0,
	drive_names: {},
	notification_count: 0,
	ripping_enabled: true,
	transcoder_online: false,
	transcoder_stats: null,
	transcoder_system_stats: null,
	active_transcodes: [],
	system_stats: null,
	transcoder_info: null
};

/** Singleton dashboard store — survives page navigations, retains last-known data. */
export const dashboard = createPollingStore(fetchDashboard, emptyDashboard, 5000);
