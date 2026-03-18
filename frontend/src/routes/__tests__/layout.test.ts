import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, cleanup } from '$lib/test-utils';
import Layout from '../+layout.svelte';
import { createRawSnippet } from 'svelte';

vi.mock('$app/stores', () => {
	const { readable } = require('svelte/store');
	return { page: readable({ url: { pathname: '/' }, params: {} }) };
});

vi.mock('$lib/stores/theme', () => {
	const { writable } = require('svelte/store');
	return { theme: writable('dark'), toggleTheme: vi.fn() };
});

vi.mock('$lib/stores/colorScheme', () => {
	const { writable } = require('svelte/store');
	return {
		colorScheme: writable('default'),
		schemeLocksMode: writable(false),
		loadThemesFromApi: vi.fn()
	};
});

vi.mock('$lib/stores/dashboard', () => {
	const { writable } = require('svelte/store');
	const store = writable({
		db_available: true, arm_online: true, active_jobs: [], system_info: null,
		drives_online: 0, drive_names: {}, notification_count: 0, ripping_enabled: true,
		transcoder_online: false, transcoder_stats: null, transcoder_system_stats: null,
		active_transcodes: [], system_stats: null, transcoder_info: null
	});
	return { dashboard: { ...store, start: vi.fn(), stop: vi.fn(), error: writable(null) } };
});

vi.mock('$lib/api/dashboard', () => ({
	setRippingEnabled: vi.fn(() => Promise.resolve())
}));

function childSnippet() {
	return createRawSnippet(() => ({
		render: () => '<p>Page Content</p>'
	}));
}

describe('Layout', () => {
	afterEach(() => cleanup());

	it('renders navigation links', () => {
		renderComponent(Layout, { props: { children: childSnippet() } });
		expect(screen.getByText('Dashboard')).toBeInTheDocument();
		expect(screen.getByText('Logs')).toBeInTheDocument();
		expect(screen.getByText('Files')).toBeInTheDocument();
		expect(screen.getByText('Settings')).toBeInTheDocument();
	});

	it('renders children content', () => {
		renderComponent(Layout, { props: { children: childSnippet() } });
		expect(screen.getByText('Page Content')).toBeInTheDocument();
	});

	it('renders ARM logo', () => {
		renderComponent(Layout, { props: { children: childSnippet() } });
		const logos = screen.getAllByAltText('ARM');
		expect(logos.length).toBeGreaterThanOrEqual(1);
	});
});
