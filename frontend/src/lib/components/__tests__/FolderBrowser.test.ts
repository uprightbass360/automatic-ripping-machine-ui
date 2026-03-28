import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup, waitFor } from '$lib/test-utils';
import FolderBrowser from '../FolderBrowser.svelte';

import { fetchIngressRoot, fetchIngressDirectory } from '$lib/api/folder';

vi.mock('$lib/api/folder', () => ({
	fetchIngressRoot: vi.fn(() => Promise.resolve([
		{ key: 'ingress', label: 'Ingress', path: '/home/arm/ingress' }
	])),
	fetchIngressDirectory: vi.fn(() => Promise.resolve({
		path: '/home/arm/ingress',
		entries: [
			{ name: 'Movie_Folder', type: 'directory', size: 4294967296, modified: '2025-06-15T12:00:00Z', extension: '', category: 'directory', permissions: 'rwxr-xr-x', owner: 'arm', group: 'arm' },
			{ name: 'TV_Show', type: 'directory', size: 2147483648, modified: '2025-06-14T10:00:00Z', extension: '', category: 'directory', permissions: 'rwxr-xr-x', owner: 'arm', group: 'arm' }
		]
	}))
}));

vi.mock('$app/navigation', () => ({ goto: vi.fn() }));

vi.mock('$lib/stores/importWizard', () => {
	const { writable } = require('svelte/store');
	return { showImportWizard: writable(false) };
});

const mockFetchIngressDirectory = vi.mocked(fetchIngressDirectory);

// jsdom does not implement scrollTo
HTMLElement.prototype.scrollTo = vi.fn();

describe('FolderBrowser', () => {
	afterEach(() => {
		cleanup();
		vi.clearAllMocks();
	});

	it('renders path bar with current path', async () => {
		renderComponent(FolderBrowser, { onselect: vi.fn() });
		await waitFor(() => {
			expect(screen.getByText('/home/arm/ingress')).toBeInTheDocument();
		});
	});

	it('renders directory entries in table', async () => {
		renderComponent(FolderBrowser, { onselect: vi.fn() });
		await waitFor(() => {
			expect(screen.getByText('Movie_Folder')).toBeInTheDocument();
			expect(screen.getByText('TV_Show')).toBeInTheDocument();
		});
	});

	it('shows .. row when navigated past root', async () => {
		mockFetchIngressDirectory.mockResolvedValueOnce({
			path: '/home/arm/ingress',
			entries: [
				{ name: 'Movie_Folder', type: 'directory', size: 4294967296, modified: '2025-06-15T12:00:00Z', extension: '', category: 'directory', permissions: 'rwxr-xr-x', owner: 'arm', group: 'arm' }
			]
		} as any).mockResolvedValueOnce({
			path: '/home/arm/ingress/Movie_Folder',
			entries: [
				{ name: 'Subfolder', type: 'directory', size: 1024, modified: '2025-06-15T12:00:00Z', extension: '', category: 'directory', permissions: 'rwxr-xr-x', owner: 'arm', group: 'arm' }
			]
		} as any);

		renderComponent(FolderBrowser, { onselect: vi.fn() });
		await waitFor(() => {
			expect(screen.getByText('Movie_Folder')).toBeInTheDocument();
		});

		// Double-click to navigate into Movie_Folder
		await fireEvent.dblClick(screen.getByText('Movie_Folder'));
		await waitFor(() => {
			expect(screen.getByText('..')).toBeInTheDocument();
		});
	});

	it('clicking .. navigates up', async () => {
		mockFetchIngressDirectory.mockResolvedValueOnce({
			path: '/home/arm/ingress',
			entries: [
				{ name: 'Movie_Folder', type: 'directory', size: 4294967296, modified: '2025-06-15T12:00:00Z', extension: '', category: 'directory', permissions: 'rwxr-xr-x', owner: 'arm', group: 'arm' }
			]
		} as any).mockResolvedValueOnce({
			path: '/home/arm/ingress/Movie_Folder',
			entries: [
				{ name: 'Subfolder', type: 'directory', size: 1024, modified: '2025-06-15T12:00:00Z', extension: '', category: 'directory', permissions: 'rwxr-xr-x', owner: 'arm', group: 'arm' }
			]
		} as any);

		renderComponent(FolderBrowser, { onselect: vi.fn() });
		await waitFor(() => {
			expect(screen.getByText('Movie_Folder')).toBeInTheDocument();
		});

		await fireEvent.dblClick(screen.getByText('Movie_Folder'));
		await waitFor(() => {
			expect(screen.getByText('..')).toBeInTheDocument();
		});

		// Click the .. row to go back
		await fireEvent.click(screen.getByText('..'));
		await waitFor(() => {
			expect(mockFetchIngressDirectory).toHaveBeenCalledWith('/home/arm/ingress');
		});
	});

	it('filter input is disabled when 5 or fewer directories', async () => {
		renderComponent(FolderBrowser, { onselect: vi.fn() });
		await waitFor(() => {
			expect(screen.getByText('Movie_Folder')).toBeInTheDocument();
		});
		const filterInput = screen.getByPlaceholderText('Filter folders...');
		expect(filterInput).toBeDisabled();
	});

	it('sort buttons render in table header', async () => {
		renderComponent(FolderBrowser, { onselect: vi.fn() });
		await waitFor(() => {
			expect(screen.getByText('Movie_Folder')).toBeInTheDocument();
		});
		// Sort buttons contain the text Name, Size, Modified (possibly with sort indicator)
		expect(screen.getByText(/^Name/)).toBeInTheDocument();
		expect(screen.getByText(/^Size/)).toBeInTheDocument();
		expect(screen.getByText(/^Modified/)).toBeInTheDocument();
	});

	it('shows empty state in table when no directories', async () => {
		mockFetchIngressDirectory.mockResolvedValueOnce({
			path: '/home/arm/ingress',
			entries: []
		} as any);

		renderComponent(FolderBrowser, { onselect: vi.fn() });
		await waitFor(() => {
			expect(screen.getByText('No subdirectories found.')).toBeInTheDocument();
		});
	});

	it('shows loading text before directory loads', async () => {
		// Make the directory fetch hang indefinitely
		mockFetchIngressDirectory.mockImplementationOnce(() => new Promise(() => {}));

		renderComponent(FolderBrowser, { onselect: vi.fn() });

		await waitFor(() => {
			expect(screen.getByText('Loading...')).toBeInTheDocument();
		});
	});
});
