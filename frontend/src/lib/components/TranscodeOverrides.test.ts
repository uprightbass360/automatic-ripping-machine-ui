import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, cleanup, waitFor } from '$lib/test-utils';
import TranscodeOverrides from './TranscodeOverrides.svelte';
import { createJob } from './__fixtures__/job';

vi.mock('$lib/api/jobs', () => ({
	updateJobTranscodeConfig: vi.fn(() => Promise.resolve())
}));

vi.mock('$lib/api/settings', () => ({
	fetchSettings: vi.fn(() => Promise.resolve({
		transcoder_config: {
			config: {
				video_encoder: 'x265',
				video_quality: 20,
				audio_encoder: 'aac',
				subtitle_mode: 'none',
				handbrake_preset: 'HQ 1080p30 Surround',
				handbrake_preset_4k: null,
				handbrake_preset_dvd: null,
				handbrake_preset_file: null,
				delete_source: false,
				output_extension: 'mkv'
			}
		}
	}))
}));

describe('TranscodeOverrides', () => {
	afterEach(() => cleanup());

	describe('rendering', () => {
		it('shows loading state initially', () => {
			renderComponent(TranscodeOverrides, {
				props: { job: createJob() }
			});
			expect(screen.getByText('Loading transcoder settings...')).toBeInTheDocument();
		});

		it('renders form fields after settings load', async () => {
			renderComponent(TranscodeOverrides, {
				props: { job: createJob() }
			});
			await waitFor(() => {
				expect(screen.getByText('Video Encoder')).toBeInTheDocument();
				expect(screen.getByText('Video Quality')).toBeInTheDocument();
				expect(screen.getByText('Audio Encoder')).toBeInTheDocument();
			});
		});

		it('shows save button', async () => {
			renderComponent(TranscodeOverrides, {
				props: { job: createJob() }
			});
			await waitFor(() => {
				expect(screen.getByText('Save Overrides')).toBeInTheDocument();
			});
		});

		it('shows global defaults', async () => {
			renderComponent(TranscodeOverrides, {
				props: { job: createJob() }
			});
			await waitFor(() => {
				expect(screen.getByText(/x265/)).toBeInTheDocument();
			});
		});
	});
});
