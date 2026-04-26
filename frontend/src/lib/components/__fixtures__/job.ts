import type { Job, JobDetail, Track } from '$lib/types/arm';

const jobDefaults: Job = {
	job_id: 1,
	arm_version: '2.0',
	crc_id: null,
	logfile: null,
	start_time: '2025-06-15T10:00:00Z',
	stop_time: null,
	job_length: null,
	status: 'ripping',
	stage: 'Ripping track 1',
	no_of_titles: 3,
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
	track_counts: null,
	tvdb_id: null
};

export function createJob(overrides: Partial<Job> = {}): Job {
	return { ...jobDefaults, ...overrides };
}

const trackDefaults: Track = {
	track_id: 1,
	job_id: 1,
	track_number: '0',
	length: 2750,
	filename: 't00.mkv',
	orig_filename: null,
	new_filename: null,
	status: null,
	error: null,
	source: null,
	enabled: true,
	aspect_ratio: '16:9',
	fps: 23.976,
	ripped: false,
	basename: null,
	title: null,
	year: null,
	imdb_id: null,
	video_type: null,
	poster_url: null,
	episode_number: null,
	episode_name: null,
	custom_filename: null
};

export function createTrack(overrides: Partial<Track> = {}): Track {
	return { ...trackDefaults, ...overrides };
}

export function createJobDetail(overrides: Partial<JobDetail> = {}): JobDetail {
	const { tracks = [], config = null, ...jobOverrides } = overrides;
	return { ...createJob(jobOverrides), tracks, config };
}
