import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup, waitFor } from '$lib/test-utils';
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

	it('renders a skeleton card when primary data prop is omitted', () => {
		const { container } = renderComponent(TranscodeCard, { props: {} });
		expect(container.querySelector('[aria-busy="true"]')).not.toBeNull();
	});

	describe('collapsed state', () => {
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
			const matches = screen.getAllByText('Transcoding');
			expect(matches.length).toBeGreaterThanOrEqual(1);
		});

		it('shows elapsed time', () => {
			renderComponent(TranscodeCard, { props: { job: createTranscodeJob() } });
			expect(screen.getByText('1h 55m')).toBeInTheDocument();
		});

		it('shows error indicator when job has error', () => {
			renderComponent(TranscodeCard, {
				props: { job: createTranscodeJob({ error: 'Encode failed' }) }
			});
			expect(screen.getByTitle('Encode failed')).toBeInTheDocument();
		});

		it('does not show expanded detail by default', () => {
			renderComponent(TranscodeCard, { props: { job: createTranscodeJob() } });
			expect(screen.queryByText('View full details')).not.toBeInTheDocument();
		});
	});

	describe('expanded state', () => {
		beforeEach(() => {
			vi.useRealTimers(); // slide transition needs real timers
		});

		it('shows detail table on click', async () => {
			renderComponent(TranscodeCard, { props: { job: createTranscodeJob() } });
			await fireEvent.click(screen.getByText('My Movie'));
			await waitFor(() => {
				expect(screen.getByText('my_movie.mkv')).toBeInTheDocument();
			});
		});

		it('shows view full details link when arm_job_id is set', async () => {
			renderComponent(TranscodeCard, { props: { job: createTranscodeJob({ arm_job_id: '42' }) } });
			await fireEvent.click(screen.getByText('My Movie'));
			await waitFor(() => {
				expect(screen.getByText('View full details')).toBeInTheDocument();
			});
		});

		it('hides view full details link when arm_job_id is null', async () => {
			renderComponent(TranscodeCard, { props: { job: createTranscodeJob() } });
			await fireEvent.click(screen.getByText('My Movie'));
			await waitFor(() => {
				expect(screen.queryByText('View full details')).not.toBeInTheDocument();
			});
		});

		it('shows source filename in expanded table', async () => {
			renderComponent(TranscodeCard, { props: { job: createTranscodeJob() } });
			await fireEvent.click(screen.getByText('My Movie'));
			await waitFor(() => {
				expect(screen.getByText('my_movie.mkv')).toBeInTheDocument();
			});
		});

		it('shows progress percentage in expanded table', async () => {
			renderComponent(TranscodeCard, { props: { job: createTranscodeJob({ progress: 45 }) } });
			await fireEvent.click(screen.getByText('My Movie'));
			await waitFor(() => {
				const matches = screen.getAllByText('45%');
				expect(matches.length).toBeGreaterThanOrEqual(1);
			});
		});

		it('shows error text when expanded', async () => {
			renderComponent(TranscodeCard, {
				props: { job: createTranscodeJob({ error: 'Encode failed' }) }
			});
			await fireEvent.click(screen.getByText('My Movie'));
			await waitFor(() => {
				expect(screen.getByText('Encode failed')).toBeInTheDocument();
			});
		});

		it('shows ARM job ID when present', async () => {
			renderComponent(TranscodeCard, {
				props: { job: createTranscodeJob({ arm_job_id: '42' }) }
			});
			await fireEvent.click(screen.getByText('My Movie'));
			await waitFor(() => {
				expect(screen.getByText('(ARM #42)')).toBeInTheDocument();
			});
		});
	});
});
