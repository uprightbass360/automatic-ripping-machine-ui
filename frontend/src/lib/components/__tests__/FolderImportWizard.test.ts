import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, cleanup } from '$lib/test-utils';
import FolderImportWizard from '../FolderImportWizard.svelte';

vi.mock('$lib/api/folder', () => ({
	scanFolder: vi.fn(() => Promise.resolve({
		disc_type: 'bluray', folder_size_bytes: 25000000000, stream_count: 5,
		label: 'TEST_DISC', title_suggestion: 'Test Movie', year_suggestion: '2025',
		season: null, disc_number: null, disc_total: null
	})),
	createFolderJob: vi.fn(() => Promise.resolve({ job_id: 1 })),
	fetchIngressRoot: vi.fn(() => Promise.resolve([
		{ key: 'ingress', label: 'Ingress', path: '/home/arm/ingress' }
	])),
	fetchIngressDirectory: vi.fn(() => Promise.resolve({
		path: '/home/arm/ingress',
		entries: [
			{ name: 'Movie_Folder', type: 'directory', size: 4294967296, modified: '2025-06-15T12:00:00Z', extension: '', category: 'directory', permissions: 'rwxr-xr-x', owner: 'arm', group: 'arm' }
		]
	}))
}));

vi.mock('$lib/api/jobs', () => ({
	searchMetadata: vi.fn(() => Promise.resolve([])),
	fetchMediaDetail: vi.fn(() => Promise.resolve({}))
}));

vi.mock('$app/navigation', () => ({ goto: vi.fn() }));

vi.mock('$lib/stores/importWizard', async () => {
	const { writable } = await import('svelte/store');
	return { showImportWizard: writable(false) };
});

describe('FolderImportWizard', () => {
	afterEach(() => {
		cleanup();
		vi.clearAllMocks();
	});

	it('renders dialog when open', () => {
		renderComponent(FolderImportWizard, {
			props: { open: true, onclose: vi.fn(), oncreated: vi.fn() }
		});
		expect(screen.getByText('Import Folder')).toBeInTheDocument();
	});

	it('shows X close button in header', () => {
		renderComponent(FolderImportWizard, {
			props: { open: true, onclose: vi.fn(), oncreated: vi.fn() }
		});
		expect(screen.getByLabelText('Close', { selector: 'button' })).toBeInTheDocument();
	});

	it('shows progress dots in footer', () => {
		const { container } = renderComponent(FolderImportWizard, {
			props: { open: true, onclose: vi.fn(), oncreated: vi.fn() }
		});
		const dots = container.querySelectorAll('.h-2.w-2.rounded-full');
		expect(dots.length).toBe(3);
	});

	it('renders folder browser on step 1', () => {
		renderComponent(FolderImportWizard, {
			props: { open: true, onclose: vi.fn(), oncreated: vi.fn() }
		});
		// The Next button is present on step 1
		expect(screen.getByText('Next')).toBeInTheDocument();
	});

	it('does not render when closed', () => {
		renderComponent(FolderImportWizard, {
			props: { open: false, onclose: vi.fn(), oncreated: vi.fn() }
		});
		expect(screen.queryByText('Import Folder')).not.toBeInTheDocument();
	});
});
