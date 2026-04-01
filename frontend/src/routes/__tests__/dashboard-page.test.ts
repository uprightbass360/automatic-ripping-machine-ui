import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, cleanup, waitFor } from '$lib/test-utils';
import DashboardPage from '../+page.svelte';

vi.mock('$lib/api/dashboard', () => ({
	fetchDashboard: vi.fn(() => Promise.resolve({
		db_available: true, arm_online: true,
		active_jobs: [
			{ job_id: 1, title: 'Ripping Movie', status: 'ripping', video_type: 'movie', year: '2024', disctype: 'bluray', label: 'TEST', start_time: '2025-06-15T10:00:00Z', stop_time: null, job_length: null, devpath: '/dev/sr0', imdb_id: null, poster_url: null, errors: null, stage: 'Ripping', no_of_titles: 3, logfile: null, tracks_total: null, tracks_ripped: null, wait_start_time: null }
		],
		system_info: null, drives_online: 1, drive_names: { '/dev/sr0': 'Main Drive' },
		notification_count: 2, ripping_enabled: true,
		transcoder_online: false, transcoder_stats: null, transcoder_system_stats: null,
		active_transcodes: [], system_stats: null, transcoder_info: null
	}))
}));

vi.mock('$lib/api/jobs', () => ({
	fetchJobs: vi.fn(() => Promise.resolve({
		jobs: [
			{ job_id: 2, title: 'Old Movie', status: 'success', video_type: 'movie', year: '2023', disctype: 'dvd', label: 'OLD', start_time: '2025-06-14T10:00:00Z', stop_time: '2025-06-14T11:00:00Z', job_length: '1h', devpath: '/dev/sr0', imdb_id: null, poster_url: null, errors: null, stage: null, no_of_titles: 1, logfile: null, tracks_total: null, tracks_ripped: null }
		],
		total: 1, page: 1, per_page: 25, pages: 1
	})),
	fetchJobProgress: vi.fn(() => Promise.resolve({ progress: null, tracks_ripped: 0, tracks_total: 0, no_of_titles: 0 })),
	abandonJob: vi.fn(),
	deleteJob: vi.fn(),
	fixJobPermissions: vi.fn()
}));

vi.mock('$lib/api/logs', () => ({
	fetchStructuredLogContent: vi.fn(() => Promise.resolve({ entries: [] }))
}));

describe('Dashboard job grouping logic', () => {
	function groupJobs(jobs: Array<{ status: string | null; job_id: number }>) {
		const scanning = jobs.filter(j => j.status?.toLowerCase() === 'identifying');
		const waiting = jobs.filter(j => j.status?.toLowerCase() === 'waiting');
		const active = jobs.filter(j => {
			const s = j.status?.toLowerCase();
			return s !== 'waiting' && s !== 'transcoding' && s !== 'waiting_transcode' && s !== 'identifying';
		});
		return { scanning, waiting, active };
	}

	it('identifying jobs go to scanning group, not active', () => {
		const jobs = [
			{ job_id: 1, status: 'identifying' },
			{ job_id: 2, status: 'ripping' },
		];
		const { scanning, active } = groupJobs(jobs);
		expect(scanning).toHaveLength(1);
		expect(scanning[0].job_id).toBe(1);
		expect(active).toHaveLength(1);
		expect(active[0].job_id).toBe(2);
	});

	it('no scanning jobs produces empty scanning group', () => {
		const jobs = [{ job_id: 1, status: 'ripping' }];
		const { scanning } = groupJobs(jobs);
		expect(scanning).toHaveLength(0);
	});

	it('multiple scanning jobs all grouped together', () => {
		const jobs = [
			{ job_id: 1, status: 'identifying' },
			{ job_id: 2, status: 'identifying' },
			{ job_id: 3, status: 'ripping' },
		];
		const { scanning, active } = groupJobs(jobs);
		expect(scanning).toHaveLength(2);
		expect(active).toHaveLength(1);
	});

	it('waiting jobs excluded from both scanning and active', () => {
		const jobs = [
			{ job_id: 1, status: 'identifying' },
			{ job_id: 2, status: 'waiting' },
			{ job_id: 3, status: 'ripping' },
		];
		const { scanning, waiting, active } = groupJobs(jobs);
		expect(scanning).toHaveLength(1);
		expect(waiting).toHaveLength(1);
		expect(active).toHaveLength(1);
	});
});

describe('Dashboard Page', () => {
	afterEach(() => cleanup());

	describe('rendering', () => {
		it('renders dashboard heading', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('Dashboard')).toBeInTheDocument();
			});
		});

		it('renders active jobs after loading', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('Ripping Movie')).toBeInTheDocument();
			});
		});

		it('renders jobs section', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('Old Movie')).toBeInTheDocument();
			});
		});
	});
});
