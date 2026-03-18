import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, cleanup, waitFor } from '$lib/test-utils';
import JobsPage from '../+page.svelte';

vi.mock('$lib/api/jobs', () => ({
	fetchJobs: vi.fn(() => Promise.resolve({
		jobs: [
			{ job_id: 1, title: 'Test Movie', status: 'success', video_type: 'movie', year: '2024', disctype: 'bluray', label: 'TEST', start_time: '2025-06-15T10:00:00Z', stop_time: '2025-06-15T11:00:00Z', job_length: '1h', devpath: '/dev/sr0', imdb_id: null, poster_url: null, errors: null, stage: null, no_of_titles: 1, logfile: null, tracks_total: null, tracks_ripped: null },
			{ job_id: 2, title: 'Another Movie', status: 'ripping', video_type: 'movie', year: '2023', disctype: 'dvd', label: 'ANOTHER', start_time: '2025-06-15T11:00:00Z', stop_time: null, job_length: null, devpath: '/dev/sr1', imdb_id: null, poster_url: null, errors: null, stage: 'Ripping', no_of_titles: 3, logfile: null, tracks_total: null, tracks_ripped: null }
		],
		total: 2,
		page: 1,
		per_page: 25,
		pages: 1
	})),
	abandonJob: vi.fn(),
	deleteJob: vi.fn(),
	fixJobPermissions: vi.fn()
}));

describe('Jobs Page', () => {
	afterEach(() => cleanup());

	describe('rendering', () => {
		it('renders page title', async () => {
			renderComponent(JobsPage);
			await waitFor(() => {
				expect(screen.getByText('Jobs')).toBeInTheDocument();
			});
		});

		it('renders jobs after loading', async () => {
			renderComponent(JobsPage);
			await waitFor(() => {
				expect(screen.getByText('Test Movie')).toBeInTheDocument();
				expect(screen.getByText('Another Movie')).toBeInTheDocument();
			});
		});

		it('renders search input', () => {
			renderComponent(JobsPage);
			expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
		});
	});
});
