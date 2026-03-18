import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup, waitFor } from '$lib/test-utils';
import DiscReviewWidget from './DiscReviewWidget.svelte';
import { createJob } from './__fixtures__/job';

vi.mock('$lib/api/jobs', () => ({
	fetchJob: vi.fn(() => Promise.resolve({
		job: { job_id: 1, title: 'Test Movie', status: 'waiting', video_type: 'movie', disctype: 'bluray', label: 'TEST', year: '2024', no_of_titles: 5, crc_id: 'abc123', logfile: 'job_1.log', start_time: '2025-06-15T10:00:00Z', wait_start_time: '2025-06-15T11:55:00Z', devpath: '/dev/sr0', imdb_id: null, poster_url: null, errors: null, multi_title: false },
		tracks: [],
		config: {}
	})),
	cancelWaitingJob: vi.fn(() => Promise.resolve()),
	startWaitingJob: vi.fn(() => Promise.resolve()),
	pauseWaitingJob: vi.fn(() => Promise.resolve()),
	updateJobTitle: vi.fn(() => Promise.resolve()),
	toggleMultiTitle: vi.fn(() => Promise.resolve()),
	updateTrack: vi.fn(() => Promise.resolve()),
	searchMetadata: vi.fn(),
	fetchMediaDetail: vi.fn(),
	searchMusicMetadata: vi.fn(),
	fetchMusicDetail: vi.fn(),
	setJobTracks: vi.fn(),
	fetchCrcLookup: vi.fn(() => Promise.resolve({ no_crc: true })),
	submitToCrcDb: vi.fn(),
	updateJobConfig: vi.fn(() => Promise.resolve()),
	updateJobTranscodeConfig: vi.fn(() => Promise.resolve())
}));

vi.mock('$lib/api/settings', () => ({
	fetchSettings: vi.fn(() => Promise.resolve({ transcoder_config: { config: {} } }))
}));

vi.mock('$lib/api/logs', () => ({
	fetchStructuredLogContent: vi.fn(() => Promise.resolve({ entries: [] })),
	fetchLogContent: vi.fn(() => Promise.resolve({ content: '' }))
}));

import { startWaitingJob, cancelWaitingJob } from '$lib/api/jobs';
const mockStart = vi.mocked(startWaitingJob);
const mockCancel = vi.mocked(cancelWaitingJob);

vi.stubGlobal('confirm', vi.fn(() => true));

describe('DiscReviewWidget', () => {
	afterEach(() => {
		cleanup();
		vi.clearAllMocks();
		vi.mocked(confirm).mockReturnValue(true);
	});

	describe('rendering', () => {
		it('renders job title after loading', async () => {
			renderComponent(DiscReviewWidget, {
				props: {
					job: createJob({ status: 'waiting', wait_start_time: '2025-06-15T11:55:00Z' })
				}
			});
			await waitFor(() => {
				expect(screen.getByText('Test Movie')).toBeInTheDocument();
			});
		});

		it('renders Start and Cancel buttons', async () => {
			renderComponent(DiscReviewWidget, {
				props: {
					job: createJob({ status: 'waiting', wait_start_time: '2025-06-15T11:55:00Z' })
				}
			});
			await waitFor(() => {
				expect(screen.getByText('Start')).toBeInTheDocument();
				expect(screen.getByText('Cancel')).toBeInTheDocument();
			});
		});

		it('renders disc type info', async () => {
			renderComponent(DiscReviewWidget, {
				props: {
					job: createJob({ status: 'waiting', disctype: 'bluray', wait_start_time: '2025-06-15T11:55:00Z' })
				}
			});
			await waitFor(() => {
				expect(screen.getByText('Blu-ray')).toBeInTheDocument();
			});
		});

		it('renders drive name from driveNames prop', async () => {
			renderComponent(DiscReviewWidget, {
				props: {
					job: createJob({ status: 'waiting', wait_start_time: '2025-06-15T11:55:00Z', devpath: '/dev/sr0' }),
					driveNames: { '/dev/sr0': 'Main Drive' }
				}
			});
			await waitFor(() => {
				expect(screen.getByText('Main Drive')).toBeInTheDocument();
			});
		});

		it('renders disc label', async () => {
			renderComponent(DiscReviewWidget, {
				props: {
					job: createJob({ status: 'waiting', wait_start_time: '2025-06-15T11:55:00Z', label: 'MOVIE_DISC' })
				}
			});
			await waitFor(() => {
				expect(screen.getByText('MOVIE_DISC')).toBeInTheDocument();
			});
		});
	});

	describe('interactions', () => {
		it('calls startWaitingJob when Start is clicked', async () => {
			renderComponent(DiscReviewWidget, {
				props: {
					job: createJob({ status: 'waiting', wait_start_time: '2025-06-15T11:55:00Z' })
				}
			});
			await waitFor(() => expect(screen.getByText('Start')).toBeInTheDocument());
			await fireEvent.click(screen.getByText('Start'));
			await waitFor(() => {
				expect(mockStart).toHaveBeenCalledWith(1);
			});
		});

		it('calls cancelWaitingJob when Cancel is clicked', async () => {
			renderComponent(DiscReviewWidget, {
				props: {
					job: createJob({ status: 'waiting', wait_start_time: '2025-06-15T11:55:00Z' })
				}
			});
			await waitFor(() => expect(screen.getByText('Cancel')).toBeInTheDocument());
			await fireEvent.click(screen.getByText('Cancel'));
			await waitFor(() => {
				expect(mockCancel).toHaveBeenCalledWith(1);
			});
		});

		it('calls ondismiss after cancel', async () => {
			const ondismiss = vi.fn();
			renderComponent(DiscReviewWidget, {
				props: {
					job: createJob({ status: 'waiting', wait_start_time: '2025-06-15T11:55:00Z' }),
					ondismiss
				}
			});
			await waitFor(() => expect(screen.getByText('Cancel')).toBeInTheDocument());
			await fireEvent.click(screen.getByText('Cancel'));
			await waitFor(() => {
				expect(ondismiss).toHaveBeenCalled();
			});
		});

		it('calls onrefresh after start', async () => {
			const onrefresh = vi.fn();
			renderComponent(DiscReviewWidget, {
				props: {
					job: createJob({ status: 'waiting', wait_start_time: '2025-06-15T11:55:00Z' }),
					onrefresh
				}
			});
			await waitFor(() => expect(screen.getByText('Start')).toBeInTheDocument());
			await fireEvent.click(screen.getByText('Start'));
			await waitFor(() => {
				expect(onrefresh).toHaveBeenCalled();
			});
		});
	});
});
