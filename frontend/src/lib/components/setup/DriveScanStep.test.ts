import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup, waitFor } from '$lib/test-utils';
import DriveScanStep from './DriveScanStep.svelte';

describe('DriveScanStep', () => {
	afterEach(() => {
		cleanup();
		vi.restoreAllMocks();
	});

	it('renders heading', () => {
		vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve([]) })));
		renderComponent(DriveScanStep);
		expect(screen.getByText('Optical Drives')).toBeInTheDocument();
	});

	it('shows no drives message when empty', async () => {
		vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve([]) })));
		renderComponent(DriveScanStep);
		await waitFor(() => {
			expect(screen.getByText('No optical drives detected')).toBeInTheDocument();
		});
	});

	it('shows drive info when drives exist', async () => {
		const drives = [
			{ drive_id: 1, name: 'Main Drive', mount: '/dev/sr0', maker: 'LG', model: 'WH16NS40', read_cd: true, read_dvd: true, read_bd: true }
		];
		vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve(drives) })));
		renderComponent(DriveScanStep);
		await waitFor(() => {
			expect(screen.getByText('Main Drive')).toBeInTheDocument();
			expect(screen.getByText('LG WH16NS40')).toBeInTheDocument();
		});
	});

	it('shows capability badges', async () => {
		const drives = [
			{ drive_id: 1, name: 'Drive', mount: '/dev/sr0', read_cd: true, read_dvd: true, read_bd: true }
		];
		vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve(drives) })));
		renderComponent(DriveScanStep);
		await waitFor(() => {
			expect(screen.getByText('CD')).toBeInTheDocument();
			expect(screen.getByText('DVD')).toBeInTheDocument();
			expect(screen.getByText('Blu-ray')).toBeInTheDocument();
		});
	});

	it('renders scan again button', async () => {
		vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve([]) })));
		renderComponent(DriveScanStep);
		await waitFor(() => {
			expect(screen.getByText('Scan Again')).toBeInTheDocument();
		});
	});

	it('shows error on fetch failure', async () => {
		vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: false })));
		renderComponent(DriveScanStep);
		await waitFor(() => {
			expect(screen.getByText('Failed to load drives')).toBeInTheDocument();
		});
	});
});
