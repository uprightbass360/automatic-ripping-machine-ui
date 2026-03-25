import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, cleanup } from '$lib/test-utils';
import EpisodeMatch from './EpisodeMatch.svelte';
import type { JobDetail, Track } from '$lib/types/arm';

vi.mock('$lib/api/jobs', () => ({
	tvdbMatch: vi.fn(() => Promise.resolve({
		success: true,
		matcher: 'runtime',
		season: 1,
		matches: [],
		match_count: 0,
		score: 0,
		alternatives: []
	})),
	fetchTvdbEpisodes: vi.fn(() => Promise.resolve({ episodes: [], tvdb_id: 12345, season: 1 })),
	updateTrack: vi.fn(() => Promise.resolve({ success: true, updated: {} })),
	fetchNamingPreview: vi.fn(() => Promise.resolve({ success: true, tracks: [] }))
}));

function createJobDetail(overrides: Partial<JobDetail> = {}): JobDetail {
	return {
		job_id: 1,
		arm_version: '2.0',
		crc_id: null,
		logfile: null,
		start_time: '2025-06-15T10:00:00Z',
		stop_time: null,
		job_length: null,
		status: 'waiting',
		stage: null,
		no_of_titles: 3,
		title: 'Test Show',
		title_auto: null,
		title_manual: null,
		year: '2024',
		year_auto: null,
		year_manual: null,
		video_type: 'series',
		video_type_auto: null,
		video_type_manual: null,
		imdb_id: 'tt1234567',
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
		label: 'TEST_SHOW',
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
		tracks: [],
		config: null,
		...overrides
	};
}

function createTrack(overrides: Partial<Track> = {}): Track {
	return {
		track_id: 1, job_id: 1, track_number: '0', length: 2750,
		filename: 't00.mkv', orig_filename: null, new_filename: null,
		status: null, error: null, source: null, enabled: true,
		aspect_ratio: '16:9', fps: 23.976, ripped: false, basename: null,
		title: null, year: null, imdb_id: null, video_type: null,
		poster_url: null, episode_number: null, episode_name: null, custom_filename: null,
		...overrides
	};
}

describe('EpisodeMatch', () => {
	afterEach(() => {
		cleanup();
		vi.clearAllMocks();
	});

	describe('empty states', () => {
		it('renders "No IMDB or TVDB ID" message when both are null', () => {
			renderComponent(EpisodeMatch, {
				props: { job: createJobDetail({ tvdb_id: null, imdb_id: null, tracks: [] }) }
			});
			expect(screen.getByText(/No IMDB or TVDB ID set/)).toBeInTheDocument();
		});

		it('renders "No tracks found" when tvdb_id set but empty tracks', () => {
			renderComponent(EpisodeMatch, {
				props: { job: createJobDetail({ tvdb_id: 12345, tracks: [] }) }
			});
			expect(screen.getByText(/No tracks found/)).toBeInTheDocument();
		});
	});

	describe('controls bar', () => {
		it('renders Season, Disc, Tolerance labels', () => {
			renderComponent(EpisodeMatch, {
				props: { job: createJobDetail() }
			});
			expect(screen.getByText('Season')).toBeInTheDocument();
			expect(screen.getByText('Disc')).toBeInTheDocument();
			expect(screen.getByText('Tolerance')).toBeInTheDocument();
		});

		it('renders Match button', () => {
			renderComponent(EpisodeMatch, {
				props: { job: createJobDetail() }
			});
			expect(screen.getByText('Match')).toBeInTheDocument();
		});

		it('season input prefills from job.season', () => {
			const { container } = renderComponent(EpisodeMatch, {
				props: { job: createJobDetail({ season: '3' }) }
			});
			const inputs = container.querySelectorAll('input[type="number"]');
			expect((inputs[0] as HTMLInputElement).value).toBe('3');
		});

		it('season input prefills from job.season_auto when season is null', () => {
			const { container } = renderComponent(EpisodeMatch, {
				props: { job: createJobDetail({ season: null, season_auto: '2' }) }
			});
			const inputs = container.querySelectorAll('input[type="number"]');
			expect((inputs[0] as HTMLInputElement).value).toBe('2');
		});

		it('disc input prefills from job.disc_number', () => {
			const { container } = renderComponent(EpisodeMatch, {
				props: { job: createJobDetail({ disc_number: 4 }) }
			});
			const inputs = container.querySelectorAll('input[type="number"]');
			expect((inputs[1] as HTMLInputElement).value).toBe('4');
		});

		it('disc total input prefills from job.disc_total', () => {
			const { container } = renderComponent(EpisodeMatch, {
				props: { job: createJobDetail({ disc_total: 6 }) }
			});
			const inputs = container.querySelectorAll('input[type="number"]');
			expect((inputs[2] as HTMLInputElement).value).toBe('6');
		});

		it('tolerance defaults to 600', () => {
			const { container } = renderComponent(EpisodeMatch, {
				props: { job: createJobDetail() }
			});
			const inputs = container.querySelectorAll('input[type="number"]');
			expect((inputs[3] as HTMLInputElement).value).toBe('600');
		});
	});

	describe('runtime conversion', () => {
		it('converts episode runtime from seconds to minutes in dropdowns', async () => {
			const { tvdbMatch, fetchTvdbEpisodes } = await import('$lib/api/jobs');
			vi.mocked(tvdbMatch).mockResolvedValueOnce({
				success: true,
				matcher: 'runtime',
				season: 1,
				matches: [
					{ track_number: '0', episode_number: 1, episode_name: 'Pilot', episode_runtime: 2700 }
				],
				match_count: 1,
				score: 100,
				alternatives: []
			});
			// API returns runtime in seconds (2700 = 45 minutes)
			vi.mocked(fetchTvdbEpisodes).mockResolvedValueOnce({
				episodes: [
					{ number: 1, name: 'Pilot', runtime: 2700, aired: '2024-01-01' },
					{ number: 2, name: 'Episode 2', runtime: 3060, aired: '2024-01-08' }
				],
				tvdb_id: 12345,
				season: 1
			});

			const { container } = renderComponent(EpisodeMatch, {
				props: { job: createJobDetail({ imdb_id: 'tt1234567', tracks: [createTrack()] }) }
			});

			// Wait for auto-match to complete
			await vi.waitFor(() => {
				const selects = container.querySelectorAll('select');
				expect(selects.length).toBeGreaterThan(0);
			});

			// Check dropdown options show minutes not seconds
			const select = container.querySelector('select')!;
			const options = Array.from(select.options);
			const pilotOption = options.find(o => o.textContent?.includes('Pilot'));
			expect(pilotOption?.textContent).toContain('45m');
			expect(pilotOption?.textContent).not.toContain('2700m');
		});

		it('shows all season episodes in dropdowns, not just matched', async () => {
			const { tvdbMatch, fetchTvdbEpisodes } = await import('$lib/api/jobs');
			vi.mocked(tvdbMatch).mockResolvedValueOnce({
				success: true,
				matcher: 'runtime',
				season: 1,
				matches: [
					{ track_number: '0', episode_number: 3, episode_name: 'Episode 3', episode_runtime: 2700 }
				],
				match_count: 1,
				score: 100,
				alternatives: []
			});
			vi.mocked(fetchTvdbEpisodes).mockResolvedValueOnce({
				episodes: [
					{ number: 1, name: 'Episode 1', runtime: 2700, aired: '' },
					{ number: 2, name: 'Episode 2', runtime: 2700, aired: '' },
					{ number: 3, name: 'Episode 3', runtime: 2700, aired: '' },
					{ number: 4, name: 'Episode 4', runtime: 2700, aired: '' },
					{ number: 5, name: 'Episode 5', runtime: 2700, aired: '' }
				],
				tvdb_id: 12345,
				season: 1
			});

			const { container } = renderComponent(EpisodeMatch, {
				props: { job: createJobDetail({ imdb_id: 'tt1234567', tracks: [createTrack()] }) }
			});

			await vi.waitFor(() => {
				const selects = container.querySelectorAll('select');
				expect(selects.length).toBeGreaterThan(0);
			});

			// All 5 episodes should be in dropdown, not just matched episode 3
			const select = container.querySelector('select')!;
			const options = Array.from(select.options).filter(o => o.value !== '');
			expect(options).toHaveLength(5);
			expect(options[0].textContent).toContain('E1');
			expect(options[4].textContent).toContain('E5');
		});

		it('deduplicates fallback episodes when fetchTvdbEpisodes fails', async () => {
			const { tvdbMatch, fetchTvdbEpisodes } = await import('$lib/api/jobs');
			vi.mocked(tvdbMatch).mockResolvedValueOnce({
				success: true,
				matcher: 'runtime',
				season: 1,
				matches: [
					{ track_number: '0', episode_number: 1, episode_name: 'Pilot', episode_runtime: 2700 },
					{ track_number: '1', episode_number: 2, episode_name: 'Ep 2', episode_runtime: 2700 }
				],
				match_count: 2,
				score: 100,
				alternatives: []
			});
			vi.mocked(fetchTvdbEpisodes).mockRejectedValueOnce(new Error('No TVDB ID'));

			const tracks = [
				createTrack(),
				createTrack({ track_id: 2, track_number: '1', filename: 't01.mkv' })
			];

			const { container } = renderComponent(EpisodeMatch, {
				props: { job: createJobDetail({ imdb_id: 'tt1234567', tracks }) }
			});

			await vi.waitFor(() => {
				const selects = container.querySelectorAll('select');
				expect(selects.length).toBeGreaterThan(0);
			});

			// Should have 2 fallback episodes from match results
			const select = container.querySelector('select')!;
			const options = Array.from(select.options).filter(o => o.value !== '');
			expect(options).toHaveLength(2);
		});
	});
});
