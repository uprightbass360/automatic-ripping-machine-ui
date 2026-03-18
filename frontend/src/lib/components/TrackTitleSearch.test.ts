import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup, waitFor } from '$lib/test-utils';
import TrackTitleSearch from './TrackTitleSearch.svelte';
import type { Track } from '$lib/types/arm';

vi.mock('$lib/api/jobs', () => ({
	searchMetadata: vi.fn(),
	fetchMediaDetail: vi.fn(),
	updateTrackTitle: vi.fn(() => Promise.resolve()),
	clearTrackTitle: vi.fn(() => Promise.resolve())
}));

import { searchMetadata } from '$lib/api/jobs';
const mockSearchMetadata = vi.mocked(searchMetadata);

function createTrack(overrides: Partial<Track> = {}): Track {
	return {
		track_id: 1,
		job_id: 1,
		track_number: '1',
		length: 7200,
		aspect_ratio: '16:9',
		fps: 24,
		enabled: true,
		basename: 'title_01',
		filename: 'title_01.mkv',
		orig_filename: 'title_01.mkv',
		new_filename: null,
		ripped: false,
		status: null,
		error: null,
		source: null,
		title: 'Track Title',
		year: '2024',
		imdb_id: null,
		poster_url: null,
		video_type: null,
		episode_number: null,
		episode_name: null,
		...overrides
	};
}

describe('TrackTitleSearch', () => {
	afterEach(() => {
		cleanup();
		vi.clearAllMocks();
	});

	describe('rendering', () => {
		it('renders search form with pre-filled track title', () => {
			renderComponent(TrackTitleSearch, {
				props: { jobId: 1, track: createTrack() }
			});
			expect(screen.getByDisplayValue('Track Title')).toBeInTheDocument();
		});

		it('renders search button', () => {
			renderComponent(TrackTitleSearch, {
				props: { jobId: 1, track: createTrack() }
			});
			expect(screen.getByText('Search')).toBeInTheDocument();
		});

		it('falls back to basename when no title', () => {
			renderComponent(TrackTitleSearch, {
				props: { jobId: 1, track: createTrack({ title: null, basename: 'title_02' }) }
			});
			expect(screen.getByDisplayValue('title_02')).toBeInTheDocument();
		});
	});

	describe('interactions', () => {
		it('calls searchMetadata on search', async () => {
			mockSearchMetadata.mockResolvedValue([
				{ title: 'Found Title', year: '2024', imdb_id: 'tt2222', poster_url: null, media_type: 'movie', plot: null, background_url: null }
			]);
			renderComponent(TrackTitleSearch, {
				props: { jobId: 1, track: createTrack() }
			});
			await fireEvent.click(screen.getByText('Search'));
			await waitFor(() => {
				expect(screen.getByText('Found Title')).toBeInTheDocument();
			});
		});
	});
});
