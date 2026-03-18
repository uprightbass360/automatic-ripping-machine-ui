import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, cleanup } from '$lib/test-utils';
import TranscoderPage from '../+page.svelte';

vi.mock('$lib/api/transcoder', () => ({
	fetchTranscoderStats: vi.fn(() => Promise.resolve({
		online: true,
		stats: { pending: 2, processing: 1, completed: 10, failed: 0, cancelled: 0, worker_running: true, current_job: null }
	})),
	fetchTranscoderJobs: vi.fn(() => Promise.resolve({
		jobs: [
			{ id: 1, title: 'Movie 1', source_path: '/raw/movie1.mkv', status: 'processing', progress: 50, error: null, logfile: 'tc_1.log', video_type: 'movie', year: '2024', disctype: 'bluray', arm_job_id: null, output_path: null, total_tracks: null, poster_url: null, config_overrides: null, created_at: '2025-06-15T10:00:00Z', started_at: '2025-06-15T10:05:00Z', completed_at: null }
		],
		total: 1
	})),
	retryTranscoderJob: vi.fn(),
	deleteTranscoderJob: vi.fn(),
	retranscodeTranscoderJob: vi.fn()
}));

vi.mock('$lib/api/logs', () => ({
	fetchStructuredTranscoderLogContent: vi.fn(() => Promise.resolve({ entries: [] })),
	fetchStructuredLogContent: vi.fn(() => Promise.resolve({ entries: [] }))
}));

describe('Transcoder Page', () => {
	afterEach(() => cleanup());

	describe('rendering', () => {
		it('renders page title', () => {
			renderComponent(TranscoderPage);
			expect(screen.getByText('Transcoder')).toBeInTheDocument();
		});

		it('renders without crashing', () => {
			const { container } = renderComponent(TranscoderPage);
			expect(container).toBeInTheDocument();
		});
	});
});
