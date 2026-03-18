import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup, waitFor } from '$lib/test-utils';
import MusicSearch from './MusicSearch.svelte';
import { createJob } from './__fixtures__/job';

vi.mock('$lib/api/jobs', () => ({
	searchMusicMetadata: vi.fn(),
	fetchMusicDetail: vi.fn(),
	updateJobTitle: vi.fn(() => Promise.resolve()),
	setJobTracks: vi.fn(() => Promise.resolve())
}));

import { searchMusicMetadata } from '$lib/api/jobs';
const mockSearchMusicMetadata = vi.mocked(searchMusicMetadata);

describe('MusicSearch', () => {
	afterEach(() => {
		cleanup();
		vi.clearAllMocks();
	});

	describe('rendering', () => {
		it('renders search form with pre-filled album/title', () => {
			renderComponent(MusicSearch, {
				props: { job: createJob({ album: 'My Album', title: 'Fallback' }) }
			});
			expect(screen.getByDisplayValue('My Album')).toBeInTheDocument();
		});

		it('renders artist input pre-filled', () => {
			renderComponent(MusicSearch, {
				props: { job: createJob({ artist: 'The Band' }) }
			});
			expect(screen.getByDisplayValue('The Band')).toBeInTheDocument();
		});

		it('renders search button', () => {
			renderComponent(MusicSearch, {
				props: { job: createJob() }
			});
			expect(screen.getByText('Search')).toBeInTheDocument();
		});
	});

	describe('interactions', () => {
		it('calls searchMusicMetadata on search', async () => {
			mockSearchMusicMetadata.mockResolvedValue({
				results: [{ id: 'r1', title: 'Found Album', artist: 'Artist', year: '2024', country: 'US', format: 'CD', track_count: 12, status: 'Official', release_type: 'Album', poster_url: null }],
				total: 1
			});
			renderComponent(MusicSearch, {
				props: { job: createJob({ album: 'Search Term' }) }
			});
			await fireEvent.click(screen.getByText('Search'));
			await waitFor(() => {
				expect(mockSearchMusicMetadata).toHaveBeenCalled();
				expect(screen.getByText('Found Album')).toBeInTheDocument();
			});
		});

		it('shows no results message', async () => {
			mockSearchMusicMetadata.mockResolvedValue({ results: [], total: 0 });
			renderComponent(MusicSearch, {
				props: { job: createJob({ album: 'Nothing' }) }
			});
			await fireEvent.click(screen.getByText('Search'));
			await waitFor(() => {
				expect(screen.getByText(/No results found/)).toBeInTheDocument();
			});
		});
	});
});
