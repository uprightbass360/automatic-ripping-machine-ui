import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, cleanup, waitFor } from '$lib/test-utils';
import SettingsPage from '../+page.svelte';

vi.mock('$lib/api/settings', () => ({
	fetchSettings: vi.fn(() => Promise.resolve({
		arm_config: { RIPMETHOD: 'mkv', MINLENGTH: '120', MAXLENGTH: '99999' },
		transcoder_config: { config: { video_encoder: 'x265' }, available_presets: [] }
	})),
	saveArmConfig: vi.fn(() => Promise.resolve({ success: true })),
	saveTranscoderConfig: vi.fn(() => Promise.resolve({ success: true })),
	testMetadataKey: vi.fn(() => Promise.resolve({ success: true, message: 'OK', provider: 'omdb' })),
	testTranscoderConnection: vi.fn(() => Promise.resolve({ reachable: true, auth_ok: true, auth_required: false, gpu_support: null, worker_running: true, queue_size: 0, error: null })),
	testTranscoderWebhook: vi.fn(() => Promise.resolve({ reachable: true, secret_ok: true, secret_required: true, error: null })),
	fetchSystemInfo: vi.fn(() => Promise.resolve({ versions: {}, endpoints: {}, paths: [], database: { path: '/db', size_bytes: 1024, available: true, migration_current: null, migration_head: null, up_to_date: true }, drives: [] })),
	fetchAbcdeConfig: vi.fn(() => Promise.resolve({ content: '', path: '/etc/abcde.conf', exists: true })),
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

vi.mock('$lib/stores/theme', () => {
	const { writable } = require('svelte/store');
	return { theme: writable('dark'), toggleTheme: vi.fn() };
});

vi.mock('$lib/stores/colorScheme', () => {
	const { writable } = require('svelte/store');
	return {
		colorScheme: writable('default'),
		COLOR_SCHEMES: [{ id: 'default', label: 'Default', swatch: '#3b82f6', tokens: {} }],
		schemeLocksMode: writable(false),
		allSchemes: writable([{ id: 'default', label: 'Default', swatch: '#3b82f6', tokens: {} }]),
		loadThemesFromApi: vi.fn()
	};
});

describe('Settings Page', () => {
	afterEach(() => cleanup());

	describe('rendering', () => {
		it('renders page title', () => {
			renderComponent(SettingsPage);
			expect(screen.getByText('Settings')).toBeInTheDocument();
		});

		it('renders without crashing', () => {
			const { container } = renderComponent(SettingsPage);
			expect(container).toBeInTheDocument();
		});

		it('renders tab buttons after settings load', async () => {
			renderComponent(SettingsPage);
			await waitFor(() => {
				expect(screen.getByText('Music')).toBeInTheDocument();
			});
		});
	});
});
