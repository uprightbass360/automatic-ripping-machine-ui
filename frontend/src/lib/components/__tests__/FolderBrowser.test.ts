import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup, waitFor } from '$lib/test-utils';
import FolderBrowser from '../FolderBrowser.svelte';
import { createFolderEntry } from '../__fixtures__/files';

import { fetchIngressRoot, fetchIngressDirectory } from '$lib/api/folder';

const movieFolder = createFolderEntry('Movie_Folder');
const tvShowFolder = createFolderEntry('TV_Show', '2025-06-14T10:00:00Z');
const subFolder = createFolderEntry('Subfolder');

vi.mock('$lib/api/folder', () => ({
	fetchIngressRoot: vi.fn(() => Promise.resolve([
		{ key: 'ingress', label: 'Ingress', path: '/home/arm/ingress' }
	])),
	fetchIngressDirectory: vi.fn(() => Promise.resolve({
		path: '/home/arm/ingress',
		entries: [movieFolder, tvShowFolder]
	}))
}));

vi.mock('$app/navigation', () => ({ goto: vi.fn() }));

vi.mock('$lib/stores/importWizard', async () => {
	const { writable } = await import('svelte/store');
	return { showImportWizard: writable(false) };
});

const mockFetchIngressDirectory = vi.mocked(fetchIngressDirectory);

// jsdom does not implement scrollTo
HTMLElement.prototype.scrollTo = vi.fn();

function renderBrowser() {
	return renderComponent(FolderBrowser, { onselect: vi.fn() });
}

async function waitForEntries() {
	await waitFor(() => {
		expect(screen.getByText('Movie_Folder')).toBeInTheDocument();
	});
}

/** Navigate into Movie_Folder and wait for the ".." back-row to appear. */
async function navigateIntoSubfolder() {
	mockFetchIngressDirectory.mockResolvedValueOnce({
		path: '/home/arm/ingress',
		entries: [{ ...movieFolder, size: 4294967296 }]
	} as any).mockResolvedValueOnce({
		path: '/home/arm/ingress/Movie_Folder',
		entries: [{ ...subFolder, size: 1024 }]
	} as any);

	renderBrowser();
	await waitForEntries();

	await fireEvent.dblClick(screen.getByText('Movie_Folder'));
	await waitFor(() => {
		expect(screen.getByText('..')).toBeInTheDocument();
	});
}

describe('FolderBrowser', () => {
	afterEach(() => {
		cleanup();
		vi.clearAllMocks();
	});

	it('renders path bar with current path', async () => {
		renderBrowser();
		await waitFor(() => {
			expect(screen.getByText('/home/arm/ingress')).toBeInTheDocument();
		});
	});

	it('renders directory entries in table', async () => {
		renderBrowser();
		await waitFor(() => {
			expect(screen.getByText('Movie_Folder')).toBeInTheDocument();
			expect(screen.getByText('TV_Show')).toBeInTheDocument();
		});
	});

	it('shows .. row when navigated past root', async () => {
		await navigateIntoSubfolder();
		// ".." is already asserted inside navigateIntoSubfolder
	});

	it('clicking .. navigates up', async () => {
		await navigateIntoSubfolder();

		await fireEvent.click(screen.getByText('..'));
		await waitFor(() => {
			expect(mockFetchIngressDirectory).toHaveBeenCalledWith('/home/arm/ingress');
		});
	});

	it('filter input is disabled when 5 or fewer directories', async () => {
		renderBrowser();
		await waitForEntries();
		const filterInput = screen.getByPlaceholderText('Filter folders...');
		expect(filterInput).toBeDisabled();
	});

	it('sort buttons render in table header', async () => {
		renderBrowser();
		await waitForEntries();
		expect(screen.getByText(/^Name/)).toBeInTheDocument();
		expect(screen.getByText(/^Size/)).toBeInTheDocument();
		expect(screen.getByText(/^Modified/)).toBeInTheDocument();
	});

	it('shows empty state in table when no directories', async () => {
		mockFetchIngressDirectory.mockResolvedValueOnce({
			path: '/home/arm/ingress',
			entries: []
		} as any);

		renderBrowser();
		await waitFor(() => {
			expect(screen.getByText('No subdirectories found.')).toBeInTheDocument();
		});
	});

	it('shows loading text before directory loads', async () => {
		mockFetchIngressDirectory.mockImplementationOnce(() => new Promise(() => {}));

		renderBrowser();

		await waitFor(() => {
			expect(screen.getByText('Loading...')).toBeInTheDocument();
		});
	});
});
