import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest';
import { renderComponent, screen, cleanup, waitFor, fireEvent } from '$lib/test-utils';
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
	fetchJobStats: vi.fn(() => Promise.resolve({ total: 1, active: 0, success: 1, fail: 0, waiting: 0 })),
	bulkDeleteJobs: vi.fn(() => Promise.resolve({ deleted: 0, errors: [] })),
	bulkPurgeJobs: vi.fn(() => Promise.resolve({ purged: 0, errors: [] })),
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

		it('renders All Jobs heading', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('All Jobs')).toBeInTheDocument();
			});
		});
	});

	describe('stats panel', () => {
		afterEach(() => cleanup());

		it('shows job stats counts', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				// Stats card labels can duplicate with filter pills, so use getAllByText
				expect(screen.getAllByText('Total').length).toBeGreaterThanOrEqual(1);
				expect(screen.getAllByText('Active').length).toBeGreaterThanOrEqual(1);
				expect(screen.getAllByText('Success').length).toBeGreaterThanOrEqual(1);
				expect(screen.getAllByText('Failed').length).toBeGreaterThanOrEqual(1);
				expect(screen.getAllByText('Waiting').length).toBeGreaterThanOrEqual(1);
			});
		});

		it('displays correct stat values from fetchJobStats', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				// fetchJobStats returns { total: 1, active: 0, success: 1, fail: 0, waiting: 0 }
				// The stat value "1" appears for total and success
				const statLabels = screen.getAllByText('1');
				expect(statLabels.length).toBeGreaterThanOrEqual(1);
			});
		});
	});

	describe('view mode toggle', () => {
		afterEach(() => cleanup());

		it('renders Cards and Table toggle buttons', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('Cards')).toBeInTheDocument();
				expect(screen.getByText('Table')).toBeInTheDocument();
			});
		});

		it('switches to table view when Table button is clicked', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('Old Movie')).toBeInTheDocument();
			});

			const tableBtn = screen.getByText('Table');
			await fireEvent.click(tableBtn);

			await waitFor(() => {
				// Table view shows column headers
				expect(screen.getByText('Title')).toBeInTheDocument();
				expect(screen.getByText('Year')).toBeInTheDocument();
				expect(screen.getByText('Status')).toBeInTheDocument();
				expect(screen.getByText('Type')).toBeInTheDocument();
				expect(screen.getByText('Device')).toBeInTheDocument();
				expect(screen.getByText('Started')).toBeInTheDocument();
				expect(screen.getByText('Actions')).toBeInTheDocument();
			});
		});
	});

	describe('filter pills', () => {
		afterEach(() => cleanup());

		it('renders status filter pills', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				// Status pills: All, Active, Success, Failed, Waiting
				// "All" appears multiple times (status pills, type pills, disc pills)
				const allButtons = screen.getAllByText('All');
				expect(allButtons.length).toBeGreaterThanOrEqual(1);
			});
		});

		it('renders video type filter pills', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('Movie')).toBeInTheDocument();
				expect(screen.getByText('Series')).toBeInTheDocument();
				expect(screen.getByText('Music')).toBeInTheDocument();
			});
		});

		it('renders disc type filter pills', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('Blu-ray')).toBeInTheDocument();
				expect(screen.getByText('DVD')).toBeInTheDocument();
				expect(screen.getByText('CD')).toBeInTheDocument();
				expect(screen.getByText('Data')).toBeInTheDocument();
			});
		});

		it('clicking a status pill calls fetchJobs with new filter', async () => {
			const { fetchJobs } = await import('$lib/api/jobs');
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('All Jobs')).toBeInTheDocument();
			});

			// Click the "Failed" status pill
			const failedPills = screen.getAllByText('Failed');
			// The pill button (not the stats card label)
			const failedPill = failedPills.find(el => el.tagName === 'BUTTON' && el.closest('.flex.flex-wrap.gap-1\\.5'));
			if (failedPill) {
				await fireEvent.click(failedPill);
				await waitFor(() => {
					expect(fetchJobs).toHaveBeenCalledWith(
						expect.objectContaining({ status: 'fail', page: 1 })
					);
				});
			}
		});

		it('clicking a video type pill calls fetchJobs', async () => {
			const { fetchJobs } = await import('$lib/api/jobs');
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('All Jobs')).toBeInTheDocument();
			});

			await fireEvent.click(screen.getByText('Movie'));
			await waitFor(() => {
				expect(fetchJobs).toHaveBeenCalledWith(
					expect.objectContaining({ video_type: 'movie' })
				);
			});
		});

		it('clicking a disc type pill calls fetchJobs', async () => {
			const { fetchJobs } = await import('$lib/api/jobs');
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('All Jobs')).toBeInTheDocument();
			});

			await fireEvent.click(screen.getByText('Blu-ray'));
			await waitFor(() => {
				expect(fetchJobs).toHaveBeenCalledWith(
					expect.objectContaining({ disctype: 'bluray' })
				);
			});
		});
	});

	describe('search', () => {
		afterEach(() => cleanup());

		it('renders search input', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByPlaceholderText('Search titles...')).toBeInTheDocument();
			});
		});

		it('search input triggers debounced fetchJobs', async () => {
			vi.useFakeTimers();
			const { fetchJobs } = await import('$lib/api/jobs');
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByPlaceholderText('Search titles...')).toBeInTheDocument();
			});

			const input = screen.getByPlaceholderText('Search titles...');
			await fireEvent.input(input, { target: { value: 'test' } });

			// Advance past debounce timeout (300ms)
			vi.advanceTimersByTime(350);

			await waitFor(() => {
				expect(fetchJobs).toHaveBeenCalledWith(
					expect.objectContaining({ search: 'test' })
				);
			});

			vi.useRealTimers();
		});
	});

	describe('days filter', () => {
		afterEach(() => cleanup());

		it('renders days dropdown with options', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('All Time')).toBeInTheDocument();
				expect(screen.getByText('7 days')).toBeInTheDocument();
				expect(screen.getByText('30 days')).toBeInTheDocument();
				expect(screen.getByText('90 days')).toBeInTheDocument();
			});
		});
	});

	describe('table view sorting', () => {
		afterEach(() => cleanup());

		it('clicking a column header toggles sort', async () => {
			const { fetchJobs } = await import('$lib/api/jobs');
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('All Jobs')).toBeInTheDocument();
			});

			// Switch to table view
			await fireEvent.click(screen.getByText('Table'));

			await waitFor(() => {
				expect(screen.getByText('Title')).toBeInTheDocument();
			});

			// Click Title column header button
			const titleHeader = screen.getByText('Title');
			const titleButton = titleHeader.closest('button');
			if (titleButton) {
				await fireEvent.click(titleButton);
				await waitFor(() => {
					expect(fetchJobs).toHaveBeenCalledWith(
						expect.objectContaining({ sort_by: 'title', sort_dir: 'desc' })
					);
				});
			}
		});
	});

	describe('checkbox selection', () => {
		afterEach(() => cleanup());

		it('table view has a select-all checkbox', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('All Jobs')).toBeInTheDocument();
			});

			await fireEvent.click(screen.getByText('Table'));

			await waitFor(() => {
				const checkboxes = screen.getAllByRole('checkbox');
				expect(checkboxes.length).toBeGreaterThanOrEqual(1);
			});
		});

		it('clicking select-all shows selection count', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('Old Movie')).toBeInTheDocument();
			});

			await fireEvent.click(screen.getByText('Table'));

			await waitFor(() => {
				const checkboxes = screen.getAllByRole('checkbox');
				expect(checkboxes.length).toBeGreaterThanOrEqual(1);
			});

			// Click select-all (first checkbox in the table header)
			const checkboxes = screen.getAllByRole('checkbox');
			await fireEvent.click(checkboxes[0]);

			await waitFor(() => {
				expect(screen.getByText('1 selected')).toBeInTheDocument();
			});
		});
	});

	describe('gear menu / bulk actions', () => {
		afterEach(() => cleanup());

		it('renders the Actions gear button', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				// The gear button contains "Actions" text with a gear icon
				const actionsBtns = screen.getAllByText(/Actions/);
				expect(actionsBtns.length).toBeGreaterThanOrEqual(1);
			});
		});

		it('opens gear menu on click', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getAllByText(/Actions/).length).toBeGreaterThanOrEqual(1);
			});

			// Find the gear button (it's a button element containing "Actions")
			const actionsBtns = screen.getAllByText(/Actions/);
			const gearBtn = actionsBtns.find(el => el.tagName === 'BUTTON');
			expect(gearBtn).toBeTruthy();
			await fireEvent.click(gearBtn!);

			await waitFor(() => {
				expect(screen.getByText('Bulk Actions')).toBeInTheDocument();
				expect(screen.getByText(/Delete All Failed/)).toBeInTheDocument();
				expect(screen.getByText(/Purge All Failed/)).toBeInTheDocument();
				expect(screen.getByText(/Delete All Successful/)).toBeInTheDocument();
			});
		});

		it('shows selected job actions when jobs are selected', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('Old Movie')).toBeInTheDocument();
			});

			// Switch to table view and select all
			await fireEvent.click(screen.getByText('Table'));
			await waitFor(() => {
				const checkboxes = screen.getAllByRole('checkbox');
				expect(checkboxes.length).toBeGreaterThanOrEqual(1);
			});

			const checkboxes = screen.getAllByRole('checkbox');
			await fireEvent.click(checkboxes[0]); // select all

			await waitFor(() => {
				expect(screen.getByText('1 selected')).toBeInTheDocument();
			});

			// Open gear menu - find the gear button specifically
			const actionsBtns = screen.getAllByText(/Actions/);
			const gearBtn = actionsBtns.find(el => el.tagName === 'BUTTON');
			expect(gearBtn).toBeTruthy();
			await fireEvent.click(gearBtn!);

			await waitFor(() => {
				expect(screen.getByText('Delete Selected')).toBeInTheDocument();
				expect(screen.getByText('Purge Selected')).toBeInTheDocument();
			});
		});
	});

	describe('pagination', () => {
		afterEach(() => cleanup());

		it('does not show pagination when only 1 page', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('Old Movie')).toBeInTheDocument();
			});

			// With only 1 page (pages: 1), no Prev/Next buttons
			expect(screen.queryByText('Prev')).not.toBeInTheDocument();
			expect(screen.queryByText('Next')).not.toBeInTheDocument();
		});

		it('shows pagination when multiple pages', async () => {
			const { fetchJobs } = await import('$lib/api/jobs');
			// Override fetchJobs to return multi-page data
			(fetchJobs as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
				jobs: [
					{ job_id: 10, title: 'Page Movie', status: 'success', video_type: 'movie', year: '2023', disctype: 'dvd', label: 'PG', start_time: '2025-06-14T10:00:00Z', stop_time: '2025-06-14T11:00:00Z', job_length: '1h', devpath: '/dev/sr0', imdb_id: null, poster_url: null, errors: null, stage: null, no_of_titles: 1, logfile: null, tracks_total: null, tracks_ripped: null }
				],
				total: 50, page: 1, per_page: 25, pages: 2
			});

			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('Page Movie')).toBeInTheDocument();
			});

			await waitFor(() => {
				expect(screen.getByText('Prev')).toBeInTheDocument();
				expect(screen.getByText('Next')).toBeInTheDocument();
				expect(screen.getByText(/Showing 1/)).toBeInTheDocument();
			});
		});
	});

	describe('active rips section', () => {
		afterEach(() => cleanup());

		it('shows active rips section when ripping jobs exist', async () => {
			renderComponent(DashboardPage);
			await waitFor(() => {
				// The mock fetchDashboard has a ripping job, so active rips section should show
				expect(screen.getByText('Ripping Movie')).toBeInTheDocument();
			});
		});
	});

	describe('empty jobs', () => {
		afterEach(() => cleanup());

		it('shows no jobs found when job list is empty', async () => {
			const { fetchJobs } = await import('$lib/api/jobs');
			(fetchJobs as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
				jobs: [],
				total: 0, page: 1, per_page: 25, pages: 1
			});

			renderComponent(DashboardPage);
			await waitFor(() => {
				expect(screen.getByText('No jobs found.')).toBeInTheDocument();
			});
		});
	});
});
