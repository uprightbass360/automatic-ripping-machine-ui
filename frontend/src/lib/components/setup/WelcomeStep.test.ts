import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, cleanup, waitFor } from '$lib/test-utils';
import WelcomeStep from './WelcomeStep.svelte';
import type { SetupStatus } from '$lib/types/setup';

const mockStatus: SetupStatus = {
	db_exists: true,
	db_initialized: true,
	db_current: true,
	db_version: 'abc123',
	db_head: 'abc123',
	first_run: true,
	arm_version: '13.3.0',
	setup_steps: { database: 'complete', drives: '2 detected', settings_reviewed: 'pending' }
};

// Mock fetch for system-info and dashboard calls
vi.stubGlobal('fetch', vi.fn((url: string) => {
	if (url.includes('system-info')) {
		return Promise.resolve({ ok: true, json: () => Promise.resolve({ cpu: 'Test CPU', memory_total_gb: 16 }) });
	}
	if (url.includes('dashboard')) {
		return Promise.resolve({ ok: true, json: () => Promise.resolve({ transcoder_online: true, transcoder_stats: { pending: 0, completed: 5, worker_running: true } }) });
	}
	return Promise.resolve({ ok: false });
}));

describe('WelcomeStep', () => {
	afterEach(() => cleanup());

	it('renders welcome heading', () => {
		renderComponent(WelcomeStep, { props: { status: mockStatus } });
		expect(screen.getByText('Welcome to ARM')).toBeInTheDocument();
	});

	it('shows ARM version', () => {
		renderComponent(WelcomeStep, { props: { status: mockStatus } });
		expect(screen.getByText('13.3.0')).toBeInTheDocument();
	});

	it('shows database initialized', () => {
		renderComponent(WelcomeStep, { props: { status: mockStatus } });
		expect(screen.getByText('Initialized')).toBeInTheDocument();
	});

	it('shows not initialized when db_initialized is false', () => {
		renderComponent(WelcomeStep, { props: { status: { ...mockStatus, db_initialized: false } } });
		expect(screen.getByText('Not initialized')).toBeInTheDocument();
	});

	it('shows drives count', () => {
		renderComponent(WelcomeStep, { props: { status: mockStatus } });
		expect(screen.getByText('2 detected')).toBeInTheDocument();
	});

	it('shows transcoder status after loading', async () => {
		renderComponent(WelcomeStep, { props: { status: mockStatus } });
		await waitFor(() => {
			expect(screen.getByText('Online')).toBeInTheDocument();
		});
	});

	it('shows transcoder DB ready after loading', async () => {
		renderComponent(WelcomeStep, { props: { status: mockStatus } });
		await waitFor(() => {
			expect(screen.getByText('Ready')).toBeInTheDocument();
		});
	});

	it('shows CPU info after loading', async () => {
		renderComponent(WelcomeStep, { props: { status: mockStatus } });
		await waitFor(() => {
			expect(screen.getByText('Test CPU')).toBeInTheDocument();
		});
	});
});
