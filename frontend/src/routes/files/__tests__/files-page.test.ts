import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup, waitFor } from '$lib/test-utils';
import FilesPage from '../+page.svelte';

import { fetchRoots, fetchDirectory } from '$lib/api/files';

vi.mock('$app/stores', async () => {
	const { readable } = await import('svelte/store');
	return {
		page: readable({ url: new URL('http://localhost/files') })
	};
});

vi.mock('$lib/api/files', () => ({
	fetchRoots: vi.fn(() => Promise.resolve([
		{ key: 'raw', label: 'Raw', path: '/media/raw' },
		{ key: 'completed', label: 'Completed', path: '/media/completed' }
	])),
	fetchDirectory: vi.fn(() => Promise.resolve({
		path: '/media/raw',
		parent: null,
		entries: [
			{ name: 'movie.mkv', type: 'file', size: 4294967296, modified: '2025-06-15T12:00:00Z', extension: 'mkv', category: 'video', permissions: 'rwxr-xr-x', owner: 'arm', group: 'arm' },
			{ name: 'subfolder', type: 'directory', size: 0, modified: '2025-06-14T10:00:00Z', extension: '', category: 'directory', permissions: 'rwxr-xr-x', owner: 'arm', group: 'arm' },
			{ name: 'show.mkv', type: 'file', size: 2147483648, modified: '2025-06-13T08:00:00Z', extension: 'mkv', category: 'video', permissions: 'rwxr-xr-x', owner: 'arm', group: 'arm' }
		]
	})),
	renameFile: vi.fn(() => Promise.resolve()),
	moveFile: vi.fn(() => Promise.resolve()),
	deleteFile: vi.fn(() => Promise.resolve()),
	createDirectory: vi.fn(() => Promise.resolve()),
	fixPermissions: vi.fn(() => Promise.resolve({ fixed: 3 }))
}));

vi.stubGlobal('confirm', vi.fn(() => true));

const mockFetchDirectory = vi.mocked(fetchDirectory);

describe('Files Page', () => {
	afterEach(() => {
		cleanup();
		vi.clearAllMocks();
		vi.mocked(confirm).mockReturnValue(true);
	});

	describe('rendering', () => {
		it('renders page title', () => {
			renderComponent(FilesPage);
			expect(screen.getByText('Files')).toBeInTheDocument();
		});

		it('renders root tabs after loading', async () => {
			renderComponent(FilesPage);
			await waitFor(() => {
				const matches = screen.getAllByText('Completed');
				expect(matches.length).toBeGreaterThanOrEqual(1);
			});
		});

		it('renders tabs in rootOrder: Raw before Completed', async () => {
			renderComponent(FilesPage);
			await waitFor(() => {
				const rawTab = screen.getAllByText('Raw')[0];
				const completedTab = screen.getAllByText('Completed')[0];
				// Raw should appear before Completed in DOM order
				expect(rawTab.compareDocumentPosition(completedTab) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
			});
		});

		it('renders file listing after auto-navigation', async () => {
			renderComponent(FilesPage);
			await waitFor(() => {
				expect(screen.getByText('movie.mkv')).toBeInTheDocument();
				expect(screen.getByText('subfolder')).toBeInTheDocument();
				expect(screen.getByText('show.mkv')).toBeInTheDocument();
			});
		});

		it('renders file sizes', async () => {
			renderComponent(FilesPage);
			await waitFor(() => {
				expect(screen.getByText('4 GB')).toBeInTheDocument();
				expect(screen.getByText('2 GB')).toBeInTheDocument();
			});
		});

		it('renders checkboxes for file selection', async () => {
			renderComponent(FilesPage);
			await waitFor(() => {
				expect(screen.getByText('movie.mkv')).toBeInTheDocument();
			});
			const checkboxes = screen.getAllByRole('checkbox');
			expect(checkboxes.length).toBeGreaterThanOrEqual(3); // 3 entries
		});
	});

	describe('navigation', () => {
		it('navigates to subdirectory on click', async () => {
			renderComponent(FilesPage);
			await waitFor(() => {
				expect(screen.getByText('subfolder')).toBeInTheDocument();
			});
			// subfolder is a directory — clicking it triggers navigation
			await fireEvent.click(screen.getByText('subfolder'));
			await waitFor(() => {
				expect(mockFetchDirectory).toHaveBeenCalledWith('/media/raw/subfolder');
			});
		});

		it('switches root on tab click', async () => {
			renderComponent(FilesPage);
			await waitFor(() => {
				const matches = screen.getAllByText('Raw');
				expect(matches.length).toBeGreaterThanOrEqual(1);
			});
			await fireEvent.click(screen.getByText('Completed'));
			await waitFor(() => {
				expect(mockFetchDirectory).toHaveBeenCalledWith('/media/completed');
			});
		});
	});

	describe('error handling', () => {
		it('shows error when fetchRoots fails', async () => {
			vi.mocked(fetchRoots).mockRejectedValueOnce(new Error('Connection failed'));
			renderComponent(FilesPage);
			await waitFor(() => {
				expect(screen.getByText('Connection failed')).toBeInTheDocument();
			});
		});

		it('shows error when fetchDirectory fails', async () => {
			mockFetchDirectory.mockRejectedValueOnce(new Error('Permission denied'));
			renderComponent(FilesPage);
			await waitFor(() => {
				expect(screen.getByText('Permission denied')).toBeInTheDocument();
			});
		});
	});
});
