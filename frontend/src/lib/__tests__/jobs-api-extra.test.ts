import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

function jsonResponse(data: unknown, ok = true) {
	return { ok, status: ok ? 200 : 500, statusText: ok ? 'OK' : 'Error', json: () => Promise.resolve(data) };
}

import { toggleMultiTitle, updateTrackTitle, clearTrackTitle, tvdbMatch, fetchTvdbEpisodes, updateTrack } from '../api/jobs';

beforeEach(() => mockFetch.mockReset());

describe('toggleMultiTitle', () => {
	it('POSTs to /api/jobs/:id/multi-title', async () => {
		mockFetch.mockResolvedValue(jsonResponse({ success: true }));
		await toggleMultiTitle(1, true);
		expect(mockFetch).toHaveBeenCalledWith('/api/jobs/1/multi-title', expect.objectContaining({
			method: 'POST',
			body: JSON.stringify({ enabled: true })
		}));
	});
});

describe('updateTrackTitle', () => {
	it('PUTs to /api/jobs/:jobId/tracks/:trackId/title', async () => {
		mockFetch.mockResolvedValue(jsonResponse({ success: true }));
		await updateTrackTitle(1, 2, { title: 'New Title' });
		expect(mockFetch).toHaveBeenCalledWith('/api/jobs/1/tracks/2/title', expect.objectContaining({
			method: 'PUT',
			body: expect.stringContaining('New Title')
		}));
	});
});

describe('clearTrackTitle', () => {
	it('DELETEs /api/jobs/:jobId/tracks/:trackId/title', async () => {
		mockFetch.mockResolvedValue(jsonResponse({ success: true }));
		await clearTrackTitle(1, 3);
		expect(mockFetch).toHaveBeenCalledWith('/api/jobs/1/tracks/3/title', expect.objectContaining({ method: 'DELETE' }));
	});
});

describe('tvdbMatch', () => {
	it('POSTs to /api/jobs/:id/tvdb-match', async () => {
		mockFetch.mockResolvedValue(jsonResponse({ success: true, matches: [], match_count: 0 }));
		await tvdbMatch(1, { season: 2, apply: true });
		expect(mockFetch).toHaveBeenCalledWith('/api/jobs/1/tvdb-match', expect.objectContaining({
			method: 'POST',
			body: JSON.stringify({ season: 2, tolerance: null, apply: true, disc_number: null, disc_total: null })
		}));
	});

	it('uses null defaults when no options', async () => {
		mockFetch.mockResolvedValue(jsonResponse({ success: true, matches: [] }));
		await tvdbMatch(1);
		expect(mockFetch).toHaveBeenCalledWith('/api/jobs/1/tvdb-match', expect.objectContaining({
			body: JSON.stringify({ season: null, tolerance: null, apply: false, disc_number: null, disc_total: null })
		}));
	});
});

describe('fetchTvdbEpisodes', () => {
	it('GETs /api/jobs/:id/tvdb-episodes?season=N', async () => {
		mockFetch.mockResolvedValue(jsonResponse({ episodes: [], tvdb_id: 123, season: 1 }));
		const result = await fetchTvdbEpisodes(1, 1);
		expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/api/jobs/1/tvdb-episodes?season=1'), expect.any(Object));
		expect(result.tvdb_id).toBe(123);
	});
});

describe('updateTrack', () => {
	it('PATCHes /api/jobs/:jobId/tracks/:trackId', async () => {
		mockFetch.mockResolvedValue(jsonResponse({ success: true, updated: { enabled: false } }));
		const result = await updateTrack(1, 2, { enabled: false });
		expect(mockFetch).toHaveBeenCalledWith('/api/jobs/1/tracks/2', expect.objectContaining({
			method: 'PATCH',
			body: JSON.stringify({ enabled: false })
		}));
		expect(result.success).toBe(true);
	});
});
