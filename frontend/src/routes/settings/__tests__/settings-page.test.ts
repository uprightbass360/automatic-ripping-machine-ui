import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, cleanup, waitFor, fireEvent } from '$lib/test-utils';
import SettingsPage from '../+page.svelte';

const mockArmConfig: Record<string, string | null> = {
	RIPMETHOD: 'mkv', MINLENGTH: '120', MAXLENGTH: '99999', MAINFEATURE: 'false',
	VIDEOTYPE: 'auto', GET_VIDEO_TITLE: 'true', ARM_CHECK_UDF: 'true',
	MANUAL_WAIT: 'true', MANUAL_WAIT_TIME: '30', DRIVE_READY_TIMEOUT: '60',
	PREVENT_99: 'true', ALLOW_DUPLICATES: 'false', AUTO_EJECT: 'true',
	DELRAWFILES: 'true', RIP_POSTER: 'true', RAW_PATH: '/raw', TRANSCODE_PATH: '/transcode',
	COMPLETED_PATH: '/completed', MUSIC_PATH: '/music', MKV_ARGS: '', DATA_RIP_PARAMETERS: '',
	METADATA_PROVIDER: 'omdb', OMDB_API_KEY: 'test-key', TMDB_API_KEY: '', TVDB_API_KEY: '',
	ARM_API_KEY: '', SET_MEDIA_PERMISSIONS: 'true', CHMOD_VALUE: '777', UMASK: '000',
	SET_MEDIA_OWNER: 'false', CHOWN_USER: '', CHOWN_GROUP: '',
	MOVIE_TITLE_PATTERN: '{title} ({year})', MOVIE_FOLDER_PATTERN: '{title} ({year})',
	TV_TITLE_PATTERN: '{title} S{season}E{episode}', TV_FOLDER_PATTERN: '{title}/Season {season}',
	MUSIC_TITLE_PATTERN: '{artist} - {album}', MUSIC_FOLDER_PATTERN: '{artist}/{album}',
	GET_AUDIO_TITLE: 'true', AUDIO_FORMAT: 'flac', ABCDE_CONFIG_FILE: '/etc/abcde.conf',
	NOTIFY_RIP: 'true', NOTIFY_TRANSCODE: 'true', NOTIFY_JOBID: 'true',
	TRANSCODER_URL: 'http://localhost:8080', JSON_URL: '', APPRISE: '',
	PB_KEY: '', IFTTT_KEY: '', PO_USER_KEY: '', PO_APP_KEY: '',
	USE_DISC_LABEL_FOR_TV: 'false', GROUP_TV_DISCS_UNDER_SERIES: 'false',
	MAKEMKV_PERMA_KEY: '', ARM_CHILDREN: '1', EXTRAS_SUB: 'extras',
	TRANSCODER_WEBHOOK_SECRET: '', LOCAL_RAW_PATH: '', SHARED_RAW_PATH: '',
	RIP_SPEED_PROFILE: 'default', MUSIC_MULTI_DISC_SUBFOLDERS: 'false', MUSIC_DISC_FOLDER_PATTERN: 'Disc {disc}',
	MAKEMKV_COMMUNITY_KEYDB: 'false', MAX_CONCURRENT_MAKEMKVINFO: '1',
	TVDB_MATCH_TOLERANCE: '300', TVDB_MAX_SEASON_SCAN: '10'
};

vi.mock('$lib/api/settings', () => ({
	fetchSettings: vi.fn(() => Promise.resolve({
		arm_config: mockArmConfig,
		transcoder_config: {
			config: { video_encoder: 'x265', video_quality: 20, audio_encoder: 'aac', subtitle_mode: 'none', delete_source: false, output_extension: 'mkv' },
			available_presets: ['HQ 1080p30', 'Fast 720p']
		}
	})),
	saveArmConfig: vi.fn(() => Promise.resolve({ success: true })),
	saveTranscoderConfig: vi.fn(() => Promise.resolve({ success: true })),
	testMetadataKey: vi.fn(() => Promise.resolve({ success: true, message: 'OK', provider: 'omdb' })),
	testTranscoderConnection: vi.fn(() => Promise.resolve({ reachable: true, auth_ok: true, auth_required: false, gpu_support: null, worker_running: true, queue_size: 0, error: null })),
	testTranscoderWebhook: vi.fn(() => Promise.resolve({ reachable: true, secret_ok: true, secret_required: true, error: null })),
	fetchSystemInfo: vi.fn(() => Promise.resolve({
		versions: { arm: '2.0.0', python: '3.12' },
		endpoints: { api: { url: 'http://localhost:8888', reachable: true } },
		paths: [{ setting: 'RAW_PATH', path: '/raw', exists: true, writable: true }],
		database: { path: '/db/arm.db', size_bytes: 102400, available: true, migration_current: 'abc', migration_head: 'abc', up_to_date: true },
		drives: [{ name: 'Drive 1', mount: '/dev/sr0', maker: 'LG', model: 'WH16NS40', capabilities: ['CD', 'DVD', 'BD'], firmware: '1.0' }]
	})),
	fetchAbcdeConfig: vi.fn(() => Promise.resolve({ content: 'CDROM=/dev/sr0\nOUTPUTTYPE=flac', path: '/etc/abcde.conf', exists: true })),
	saveAbcdeConfig: vi.fn(() => Promise.resolve({ success: true }))
}));

vi.mock('$lib/api/drives', () => ({
	fetchDrives: vi.fn(() => Promise.resolve([])),
	updateDrive: vi.fn(() => Promise.resolve()),
	scanDrive: vi.fn(() => Promise.resolve()),
	deleteDrive: vi.fn(() => Promise.resolve()),
	fetchDriveDiagnostic: vi.fn(() => Promise.resolve({ success: true, drives: [], issues: [], udevd_running: true, kernel_drives: [] }))
}));

vi.mock('$lib/api/themes', () => ({
	uploadTheme: vi.fn(() => Promise.resolve()),
	deleteTheme: vi.fn(() => Promise.resolve())
}));

vi.mock('$lib/stores/theme', async () => {
	const { writable } = await import('svelte/store');
	return { theme: writable('dark'), toggleTheme: vi.fn() };
});

vi.mock('$lib/stores/colorScheme', async () => {
	const { writable } = await import('svelte/store');
	return {
		colorScheme: writable('default'),
		COLOR_SCHEMES: [{ id: 'default', label: 'Default', swatch: '#3b82f6', tokens: {}, mode: 'dark' }],
		schemeLocksMode: writable(false),
		allSchemes: writable([{ id: 'default', label: 'Default', swatch: '#3b82f6', tokens: {}, mode: 'dark' }]),
		loadThemesFromApi: vi.fn()
	};
});

vi.mock('$lib/api/system', () => ({
	restartArm: vi.fn(() => Promise.resolve()),
	restartTranscoder: vi.fn(() => Promise.resolve())
}));

vi.mock('$lib/api/dashboard', () => ({
	checkMakemkvKey: vi.fn(() => Promise.resolve({ valid: true, message: 'OK' }))
}));

vi.mock('$lib/api/maintenance', () => ({
	fetchImageCacheStats: vi.fn(() => Promise.resolve({ count: 5, size_bytes: 5242880, size_mb: '5.0' })),
	clearImageCache: vi.fn(() => Promise.resolve({ success: true, cleared: 5, freed_bytes: 5242880 }))
}));

vi.mock('$lib/stores/polling', async () => {
	const { writable } = await import('svelte/store');
	return {
		createPollingStore: vi.fn(() => ({
			subscribe: writable([]).subscribe,
			data: writable([]),
			loading: writable(false),
			error: writable(null),
			initialized: writable(true),
			refresh: vi.fn(),
			start: vi.fn(),
			stop: vi.fn()
		}))
	};
});

describe('Settings Page', () => {
	afterEach(() => cleanup());

	describe('rendering', () => {
		it('renders page title', () => {
			renderComponent(SettingsPage);
			expect(screen.getByText('Settings')).toBeInTheDocument();
		});

		it('renders all tab buttons after settings load', async () => {
			renderComponent(SettingsPage);
			await waitFor(() => {
				expect(screen.getByText('Music')).toBeInTheDocument();
			});
			const allTabs = ['Ripping', 'Music', 'Transcoding', 'Notifications', 'Drives', 'Appearance'];
			for (const tab of allTabs) {
				const matches = screen.getAllByText(tab);
				expect(matches.length).toBeGreaterThanOrEqual(1);
			}
		});

		it('renders ripping tab panel groups by default', async () => {
			renderComponent(SettingsPage);
			await waitFor(() => {
				expect(screen.getByText('Disc Identification')).toBeInTheDocument();
			});
			// These panels are collapsible buttons — check they exist
			const panelNames = ['Track Selection', 'Rip Method', 'Post-Rip', 'Media Directories', 'File Permissions', 'Naming Patterns'];
			for (const name of panelNames) {
				const matches = screen.queryAllByText(name);
				expect(matches.length, `Expected to find "${name}"`).toBeGreaterThanOrEqual(1);
			}
		});

		it('renders ARM config field values', async () => {
			renderComponent(SettingsPage);
			await waitFor(() => {
				// Check some specific config values are rendered as inputs
				expect(screen.getByDisplayValue('120')).toBeInTheDocument(); // MINLENGTH
				expect(screen.getByDisplayValue('99999')).toBeInTheDocument(); // MAXLENGTH
			});
		});

		it('renders MakeMKV panel', async () => {
			renderComponent(SettingsPage);
			await waitFor(() => {
				expect(screen.getByText('MakeMKV')).toBeInTheDocument();
			});
		});

		it('renders Metadata panel with API key fields', async () => {
			renderComponent(SettingsPage);
			await waitFor(() => {
				const matches = screen.getAllByText('Metadata');
				expect(matches.length).toBeGreaterThanOrEqual(1);
			});
		});

		it('renders TV Series panel', async () => {
			renderComponent(SettingsPage);
			await waitFor(() => {
				expect(screen.getByText('TV Series')).toBeInTheDocument();
			});
		});

		it('shows Appearance tab', async () => {
			renderComponent(SettingsPage);
			await waitFor(() => {
				expect(screen.getByText('Music')).toBeInTheDocument();
			});
			const matches = screen.getAllByText('Appearance');
			expect(matches.length).toBeGreaterThanOrEqual(1);
		});

		it('image cache section loads when Appearance tab active', async () => {
			renderComponent(SettingsPage);
			await waitFor(() => {
				expect(screen.getByText('Music')).toBeInTheDocument();
			});
			// Click Appearance tab
			const appearanceTab = screen.getAllByText('Appearance');
			await fireEvent.click(appearanceTab[0]);
			await waitFor(() => {
				expect(screen.getByText('Image Cache')).toBeInTheDocument();
			});
			// Verify cache stats are rendered
			await waitFor(() => {
				expect(screen.getByText(/5 cached images/)).toBeInTheDocument();
				expect(screen.getByText(/5\.0 MB/)).toBeInTheDocument();
			});
			// Verify Clear Cache button exists
			expect(screen.getByText('Clear Cache')).toBeInTheDocument();
		});

		it('shows cache feedback after clearing image cache', async () => {
			renderComponent(SettingsPage);
			await waitFor(() => {
				expect(screen.getByText('Music')).toBeInTheDocument();
			});
			const appearanceTab = screen.getAllByText('Appearance');
			await fireEvent.click(appearanceTab[0]);
			await waitFor(() => {
				expect(screen.getByText('Clear Cache')).toBeInTheDocument();
			});
			// Click Clear Cache to open confirm dialog
			await fireEvent.click(screen.getByText('Clear Cache'));
			// Confirm the dialog — confirmLabel is "Clear"
			await waitFor(() => {
				expect(screen.getByText('Clear Image Cache')).toBeInTheDocument();
			});
			const clearBtns = screen.getAllByText('Clear');
			await fireEvent.click(clearBtns[clearBtns.length - 1]);
			// Verify feedback message appears
			await waitFor(() => {
				expect(screen.getByText(/Cleared 5 cached images/)).toBeInTheDocument();
			});
		});

		it('shows dark mode toggle when scheme does not lock mode', async () => {
			renderComponent(SettingsPage);
			await waitFor(() => {
				expect(screen.getByText('Music')).toBeInTheDocument();
			});
			const appearanceTab = screen.getAllByText('Appearance');
			await fireEvent.click(appearanceTab[0]);
			await waitFor(() => {
				expect(screen.getByText('Dark Mode')).toBeInTheDocument();
			});
			expect(screen.getByLabelText('Dark mode')).toBeInTheDocument();
			expect(screen.getByText('Toggle between light and dark mode.')).toBeInTheDocument();
		});

		it('calls toggleTheme when dark mode switch is clicked', async () => {
			const { toggleTheme } = await import('$lib/stores/theme');
			renderComponent(SettingsPage);
			await waitFor(() => {
				expect(screen.getByText('Music')).toBeInTheDocument();
			});
			const appearanceTab = screen.getAllByText('Appearance');
			await fireEvent.click(appearanceTab[0]);
			await waitFor(() => {
				expect(screen.getByLabelText('Dark mode')).toBeInTheDocument();
			});
			await fireEvent.click(screen.getByLabelText('Dark mode'));
			expect(toggleTheme).toHaveBeenCalled();
		});

		it('shows "Locked by theme" when schemeLocksMode is true', async () => {
			const { schemeLocksMode } = await import('$lib/stores/colorScheme');
			const { writable } = await import('svelte/store');
			const locked = writable(true);
			Object.assign(schemeLocksMode, { set: locked.set, subscribe: locked.subscribe, update: locked.update });

			renderComponent(SettingsPage);
			await waitFor(() => {
				expect(screen.getByText('Music')).toBeInTheDocument();
			});
			const appearanceTab = screen.getAllByText('Appearance');
			await fireEvent.click(appearanceTab[0]);
			await waitFor(() => {
				expect(screen.getByText('Locked by theme')).toBeInTheDocument();
			});
			expect(screen.queryByLabelText('Dark mode')).not.toBeInTheDocument();
		});

		it('renders drives tab with collapsible diagnostics toggle', async () => {
			renderComponent(SettingsPage);
			await waitFor(() => {
				expect(screen.getByText('Music')).toBeInTheDocument();
			});
			// Switch to drives tab
			const drivesTab = screen.getAllByText('Drives');
			await fireEvent.click(drivesTab[0]);
			await waitFor(() => {
				expect(screen.getByText('Udev & Drive Diagnostics')).toBeInTheDocument();
			});
			// Run Check button should not be visible when collapsed
			expect(screen.queryByText('Run Check')).not.toBeInTheDocument();
		});
	});
});
