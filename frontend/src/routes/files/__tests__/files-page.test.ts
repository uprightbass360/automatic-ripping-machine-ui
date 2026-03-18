import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, cleanup, waitFor } from '$lib/test-utils';
import FilesPage from '../+page.svelte';

vi.mock('$lib/api/files', () => ({
	fetchRoots: vi.fn(() => Promise.resolve([
		{ key: 'completed', label: 'Completed', path: '/media/completed' },
		{ key: 'raw', label: 'Raw', path: '/media/raw' }
	])),
	fetchDirectory: vi.fn(() => Promise.resolve({
		path: '/media/completed',
		parent: null,
		entries: [
			{ name: 'movie.mkv', type: 'file', size: 4294967296, modified: '2025-06-15T12:00:00Z', extension: 'mkv', category: 'video' }
		]
	})),
	renameFile: vi.fn(() => Promise.resolve()),
	moveFile: vi.fn(() => Promise.resolve()),
	deleteFile: vi.fn(() => Promise.resolve()),
	createDirectory: vi.fn(() => Promise.resolve()),
	fixPermissions: vi.fn(() => Promise.resolve())
}));

describe('Files Page', () => {
	afterEach(() => cleanup());

	describe('rendering', () => {
		it('renders page title', () => {
			renderComponent(FilesPage);
			expect(screen.getByText('Files')).toBeInTheDocument();
		});

		it('renders without crashing', () => {
			const { container } = renderComponent(FilesPage);
			expect(container).toBeInTheDocument();
		});

		it('renders root buttons after loading', async () => {
			renderComponent(FilesPage);
			await waitFor(() => {
				const matches = screen.getAllByText('Completed');
				expect(matches.length).toBeGreaterThanOrEqual(1);
			});
		});
	});
});
