import { createPollingStore } from './polling';
import { fetchDashboard } from '$lib/api/dashboard';
import type { DashboardData } from '$lib/types/arm';

const emptyDashboard: DashboardData = {
	db_available: true,
	arm_online: false,
	active_jobs: [],
	system_info: null,
	drives_online: 0,
	drive_names: {},
	notification_count: 0,
	ripping_enabled: true,
	makemkv_key_valid: null,
	makemkv_key_checked_at: null,
	transcoder_online: false,
	transcoder_stats: null,
	transcoder_system_stats: null,
	active_transcodes: [],
	system_stats: null,
	transcoder_info: null
};

// Fields the BFF marks `null` when their underlying ARM endpoint blipped on
// this poll. We hold the previous value for these so a transient timeout
// doesn't flicker badges/counts to zero.
const STICKY_FIELDS = [
	'active_jobs',
	'drives_online',
	'drive_names',
	'notification_count',
	'ripping_enabled'
] as const satisfies readonly (keyof DashboardData)[];

let lastGood: DashboardData = emptyDashboard;

async function fetchDashboardSticky(): Promise<DashboardData> {
	const fresh = (await fetchDashboard()) as DashboardData & Partial<Record<(typeof STICKY_FIELDS)[number], unknown>>;
	const merged = { ...fresh } as DashboardData;
	for (const key of STICKY_FIELDS) {
		if (fresh[key] === null || fresh[key] === undefined) {
			(merged[key] as unknown) = lastGood[key];
		}
	}
	lastGood = merged;
	return merged;
}

/** Singleton dashboard store — survives page navigations, retains last-known data. */
export const dashboard = createPollingStore(fetchDashboardSticky, emptyDashboard, 5000);
