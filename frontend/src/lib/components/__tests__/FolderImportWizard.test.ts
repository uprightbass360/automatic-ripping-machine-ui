import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, cleanup, fireEvent, waitFor } from '$lib/test-utils';
import FolderImportWizard from '../FolderImportWizard.svelte';
import FolderBrowserMock from './FolderBrowserMock.svelte';

vi.mock('$lib/components/FolderBrowser.svelte', async () => ({
	default: (await import('./FolderBrowserMock.svelte')).default
}));

const searchMetadataMock = vi.fn(() => Promise.resolve([]));

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
	searchMetadata: (...args: unknown[]) => searchMetadataMock(...(args as [])),
	fetchMediaDetail: vi.fn(() => Promise.resolve({}))
}));

void FolderBrowserMock; // ensure import isn't tree-shaken

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
		// 4-step wizard: Pick Folder -> Verify metadata -> OMDB Match -> Confirm
		expect(dots.length).toBe(4);
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

	describe('4-step flow (Pick -> Verify -> OMDB -> Confirm)', () => {
		async function advanceToStep2() {
			renderComponent(FolderImportWizard, {
				props: { open: true, onclose: vi.fn(), oncreated: vi.fn() }
			});
			// Step 1: pick a folder via the mocked FolderBrowser, then click Next.
			await fireEvent.click(screen.getByTestId('folder-browser-mock-select'));
			await fireEvent.click(screen.getByText('Next'));
			// scanFolder resolves, wizard auto-advances to step 2.
			await waitFor(() => expect(screen.getByText('Looks good')).toBeInTheDocument());
		}

		it('step 2 shows both "Looks good" (skip OMDB) and "Search OMDB" buttons', async () => {
			await advanceToStep2();
			expect(screen.getByText('Looks good')).toBeInTheDocument();
			expect(screen.getByText('Search OMDB')).toBeInTheDocument();
		});

		it('"Looks good" on step 2 jumps directly to step 4 (Confirm), skipping OMDB', async () => {
			await advanceToStep2();
			await fireEvent.click(screen.getByText('Looks good'));
			// Step 4 has the Import button
			await waitFor(() => expect(screen.getByText('Import')).toBeInTheDocument());
		});

		it('"Search OMDB" on step 2 advances to step 3 and auto-fires the search', async () => {
			searchMetadataMock.mockClear();
			await advanceToStep2();
			await fireEvent.click(screen.getByText('Search OMDB'));
			// Step 3 has a "Next" button (advances to Confirm) and a search input.
			await waitFor(() => {
				expect(screen.getByPlaceholderText('Search title...')).toBeInTheDocument();
			});
			// Auto-search fires with the seeded title.
			await waitFor(() => expect(searchMetadataMock).toHaveBeenCalled());
		});
	});
});
