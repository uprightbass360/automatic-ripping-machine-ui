import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, cleanup } from '$lib/test-utils';
import EpisodeMatch from './EpisodeMatch.svelte';
import type { JobDetail } from '$lib/types/arm';

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
	updateTrack: vi.fn(() => Promise.resolve({ success: true, updated: {} }))
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

		it('tolerance defaults to 300', () => {
			const { container } = renderComponent(EpisodeMatch, {
				props: { job: createJobDetail() }
			});
			const inputs = container.querySelectorAll('input[type="number"]');
			expect((inputs[3] as HTMLInputElement).value).toBe('300');
		});
	});
});
