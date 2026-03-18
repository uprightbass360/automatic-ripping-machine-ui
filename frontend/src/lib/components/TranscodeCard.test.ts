import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderComponent, screen, cleanup } from '$lib/test-utils';
import TranscodeCard from './TranscodeCard.svelte';
import type { TranscoderJob } from '$lib/types/transcoder';

function createTranscodeJob(overrides: Partial<TranscoderJob> = {}): TranscoderJob {
	return {
		id: 1,
		title: 'My Movie',
		source_path: '/media/raw/my_movie.mkv',
		status: 'processing',
		progress: 45,
		error: null,
		logfile: null,
		video_type: 'movie',
		year: '2024',
		disctype: 'bluray',
		arm_job_id: null,
		output_path: null,
		total_tracks: null,
		poster_url: null,
		config_overrides: null,
		created_at: '2025-06-15T10:00:00Z',
		started_at: '2025-06-15T10:05:00Z',
		completed_at: null,
		...overrides
	};
}

describe('TranscodeCard', () => {
	beforeEach(() => {
		vi.useFakeTimers();
		vi.setSystemTime(new Date('2025-06-15T12:00:00Z'));
	});

	afterEach(() => {
		cleanup();
		vi.useRealTimers();
	});

	describe('rendering', () => {
		it('renders job title', () => {
			renderComponent(TranscodeCard, { props: { job: createTranscodeJob() } });
			expect(screen.getByText('My Movie')).toBeInTheDocument();
		});

		it('falls back to source filename when no title', () => {
			renderComponent(TranscodeCard, {
				props: { job: createTranscodeJob({ title: '' }) }
			});
			expect(screen.getByText('my_movie.mkv')).toBeInTheDocument();
		});

		it('falls back to Transcode # when no title or source', () => {
			renderComponent(TranscodeCard, {
				props: { job: createTranscodeJob({ title: '', source_path: '' }) }
			});
			expect(screen.getByText('Transcode #1')).toBeInTheDocument();
		});

		it('renders status badge', () => {
			renderComponent(TranscodeCard, { props: { job: createTranscodeJob() } });
			// "Transcoding" appears in both StatusBadge and status label
			const matches = screen.getAllByText('Transcoding');
			expect(matches.length).toBeGreaterThanOrEqual(1);
		});

		it('renders source filename below title', () => {
			renderComponent(TranscodeCard, { props: { job: createTranscodeJob() } });
			expect(screen.getByText('my_movie.mkv')).toBeInTheDocument();
		});

		it('shows elapsed time', () => {
			renderComponent(TranscodeCard, { props: { job: createTranscodeJob() } });
			expect(screen.getByText('1h 55m')).toBeInTheDocument();
		});

		it('shows progress bar when progress is set', () => {
			const { container } = renderComponent(TranscodeCard, {
				props: { job: createTranscodeJob({ progress: 45 }) }
			});
			expect(container.querySelector('[data-progress-track]')).toBeInTheDocument();
			expect(screen.getByText('45%')).toBeInTheDocument();
		});

		it('shows errors indicator when job has error', () => {
			renderComponent(TranscodeCard, {
				props: { job: createTranscodeJob({ error: 'Encode failed' }) }
			});
			expect(screen.getByText('errors')).toBeInTheDocument();
		});
	});
});
