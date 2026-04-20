import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup, waitFor } from '$lib/test-utils';
import Page from './+page.svelte';
import type { JobDetail } from '$lib/types/arm';

// --- Mocks ---

const mockGoto = vi.fn();
vi.mock('$app/navigation', () => ({ goto: (...args: unknown[]) => mockGoto(...args) }));

vi.mock('$app/stores', () => ({
	page: {
		subscribe: (fn: (val: { params: { id: '42' } }) => void) => {
			fn({ params: { id: '42' } });
			return () => {};
		}
	}
}));

const baseJob: JobDetail = {
	job_id: 42,
	arm_version: '2.0',
	crc_id: null,
	logfile: null,
	start_time: '2025-06-15T10:00:00Z',
	stop_time: null,
	job_length: null,
	status: 'waiting_transcode',
	stage: null,
	no_of_titles: 1,
	title: 'Test Movie',
	title_auto: null,
	title_manual: null,
	year: '2024',
	year_auto: null,
	year_manual: null,
	video_type: 'movie',
	video_type_auto: null,
	video_type_manual: null,
	imdb_id: null,
	imdb_id_auto: null,
	imdb_id_manual: null,
	poster_url: null,
	poster_url_auto: null,
	poster_url_manual: null,
	devpath: '/dev/sr0',
	mountpoint: null,
	hasnicetitle: null,
	errors: null,
	disctype: 'bluray',
	label: 'TEST_MOVIE',
	path: null,
	raw_path: null,
	transcode_path: null,
	artist: null,
	artist_auto: null,
	artist_manual: null,
	album: null,
	album_auto: null,
	album_manual: null,
	season: null,
	season_auto: null,
	season_manual: null,
	episode: null,
	episode_auto: null,
	episode_manual: null,
	transcode_overrides: null,
	multi_title: null,
	title_pattern_override: null,
	folder_pattern_override: null,
	disc_number: null,
	disc_total: null,
	ejected: null,
	pid: null,
	manual_pause: null,
	wait_start_time: null,
	tracks_total: null,
	tracks_ripped: null,
	tvdb_id: null,
	source_type: null,
	tracks: [],
	config: { MINLENGTH: '120' }
} as unknown as JobDetail;

vi.mock('$lib/api/jobs', () => ({
	fetchJob: vi.fn(() => Promise.resolve({ ...baseJob })),
	retranscodeJob: vi.fn(),
	skipAndFinalize: vi.fn(() => Promise.resolve({ success: true, message: 'Done' })),
	fetchMusicDetail: vi.fn(),
	toggleMultiTitle: vi.fn(),
	updateTrack: vi.fn(),
	fetchNamingPreview: vi.fn(() => Promise.resolve({ success: true, job_title: '', job_folder: '', tracks: [] })),
	searchMetadata: vi.fn(),
	fetchMediaDetail: vi.fn(),
	searchMusicMetadata: vi.fn(),
	setJobTracks: vi.fn(),
	fetchCrcLookup: vi.fn(),
	submitToCrcDb: vi.fn(),
	updateJobConfig: vi.fn(),
	updateJobTitle: vi.fn(),
	updateJobTranscodeConfig: vi.fn()
}));

vi.mock('$lib/api/logs', () => ({
	fetchStructuredLogContent: vi.fn(() => Promise.resolve({ entries: [] })),
	fetchStructuredTranscoderLogContent: vi.fn(() => Promise.resolve({ entries: [] })),
	fetchTranscoderLogForArmJob: vi.fn(() => Promise.resolve({ found: false })),
	fetchLogContent: vi.fn(() => Promise.resolve({ content: '' }))
}));

vi.mock('$lib/api/settings', () => ({
	fetchSettings: vi.fn(() => Promise.resolve({ transcoder_config: { config: {} } }))
}));

import { fetchJob, skipAndFinalize } from '$lib/api/jobs';
const mockFetchJob = vi.mocked(fetchJob);
const mockSkipAndFinalize = vi.mocked(skipAndFinalize);

describe('Job detail page — skip transcode', () => {
	afterEach(() => {
		cleanup();
		vi.clearAllMocks();
	});

	it('shows Skip Transcode & Finalize button for waiting_transcode status', async () => {
		mockFetchJob.mockResolvedValue({ ...baseJob, status: 'waiting_transcode' } as any);
		renderComponent(Page);
		await waitFor(() => {
			expect(screen.getByText('Skip Transcode & Finalize')).toBeInTheDocument();
		});
	});

	it('shows Skip Transcode & Finalize button for transcoding status', async () => {
		mockFetchJob.mockResolvedValue({ ...baseJob, status: 'transcoding' } as any);
		renderComponent(Page);
		await waitFor(() => {
			expect(screen.getByText('Skip Transcode & Finalize')).toBeInTheDocument();
		});
	});

	it('does NOT show skip button for other statuses', async () => {
		mockFetchJob.mockResolvedValue({ ...baseJob, status: 'success' } as any);
		renderComponent(Page);
		// Wait for page to render by checking for the breadcrumb Dashboard link
		await waitFor(() => {
			expect(screen.getByText('Dashboard')).toBeInTheDocument();
		});
		expect(screen.queryByText('Skip Transcode & Finalize')).not.toBeInTheDocument();
	});

	it('calls skipAndFinalize and shows success feedback', async () => {
		mockFetchJob.mockResolvedValue({ ...baseJob, status: 'waiting_transcode' } as any);
		mockSkipAndFinalize.mockResolvedValue({ success: true, message: 'Finalized without transcoding' });
		renderComponent(Page);
		await waitFor(() => expect(screen.getByText('Skip Transcode & Finalize')).toBeInTheDocument());
		await fireEvent.click(screen.getByText('Skip Transcode & Finalize'));
		await waitFor(() => {
			expect(mockSkipAndFinalize).toHaveBeenCalledWith(42);
		});
		await waitFor(() => {
			expect(screen.getByText('Finalized without transcoding')).toBeInTheDocument();
		});
	});

	it('shows error feedback when skipAndFinalize returns success=false', async () => {
		mockFetchJob.mockResolvedValue({ ...baseJob, status: 'waiting_transcode' } as any);
		mockSkipAndFinalize.mockResolvedValue({ success: false, error: 'Job not found' });
		renderComponent(Page);
		await waitFor(() => expect(screen.getByText('Skip Transcode & Finalize')).toBeInTheDocument());
		await fireEvent.click(screen.getByText('Skip Transcode & Finalize'));
		await waitFor(() => {
			expect(screen.getByText('Job not found')).toBeInTheDocument();
		});
	});

	it('shows error feedback when skipAndFinalize throws', async () => {
		mockFetchJob.mockResolvedValue({ ...baseJob, status: 'waiting_transcode' } as any);
		mockSkipAndFinalize.mockRejectedValue(new Error('Network error'));
		renderComponent(Page);
		await waitFor(() => expect(screen.getByText('Skip Transcode & Finalize')).toBeInTheDocument());
		await fireEvent.click(screen.getByText('Skip Transcode & Finalize'));
		await waitFor(() => {
			expect(screen.getByText('Network error')).toBeInTheDocument();
		});
	});

	it('disables button while skipping is in progress', async () => {
		mockFetchJob.mockResolvedValue({ ...baseJob, status: 'waiting_transcode' } as any);
		// Never resolve to keep button in disabled state
		mockSkipAndFinalize.mockReturnValue(new Promise(() => {}));
		renderComponent(Page);
		await waitFor(() => expect(screen.getByText('Skip Transcode & Finalize')).toBeInTheDocument());
		const button = screen.getByText('Skip Transcode & Finalize');
		await fireEvent.click(button);
		await waitFor(() => {
			expect(screen.getByText('Finalizing...')).toBeInTheDocument();
		});
		expect(screen.getByText('Finalizing...').closest('button')).toBeDisabled();
	});
});
