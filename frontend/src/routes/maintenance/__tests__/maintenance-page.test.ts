import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderComponent, screen, waitFor, fireEvent, cleanup } from '$lib/test-utils';
import MaintenancePage from '../+page.svelte';

vi.mock('$lib/api/maintenance', () => ({
	fetchSummary: vi.fn(() =>
		Promise.resolve({
			orphan_logs: 3,
			orphan_folders: 5,
			unseen_notifications: 12,
			cleared_notifications: 45,
			stale_transcoder_jobs: 8
		})
	),
	fetchOrphanLogs: vi.fn(() =>
		Promise.resolve({
			root: '/tmp/logs',
			total_size_bytes: 5242880,
			files: [
				{ path: '/tmp/logs/a.log', relative_path: 'a.log', size_bytes: 1048576 },
				{ path: '/tmp/logs/b.log', relative_path: 'b.log', size_bytes: 4194304 }
			]
		})
	),
	fetchOrphanFolders: vi.fn(() =>
		Promise.resolve({
			total_size_bytes: 1073741824,
			folders: [
				{ path: '/raw/Orphan', name: 'Orphan', category: 'raw', size_bytes: 1073741824 }
			]
		})
	),
	deleteLog: vi.fn(() => Promise.resolve({ success: true })),
	deleteFolder: vi.fn(() => Promise.resolve({ success: true })),
	bulkDeleteLogs: vi.fn(() => Promise.resolve({ removed: [], errors: [] })),
	bulkDeleteFolders: vi.fn(() => Promise.resolve({ removed: [], errors: [] })),
	dismissAllNotifications: vi.fn(() => Promise.resolve({ success: true, count: 12 })),
	purgeNotifications: vi.fn(() => Promise.resolve({ success: true, count: 45 })),
	cleanupTranscoder: vi.fn(() => Promise.resolve({ success: true, deleted: 8, errors: [] }))
}));

describe('Maintenance Page', () => {
	beforeEach(() => {
		cleanup();
		vi.clearAllMocks();
	});

	it('renders page title and section headers', async () => {
		renderComponent(MaintenancePage);
		await waitFor(() => {
			expect(screen.getByText('Maintenance')).toBeInTheDocument();
		});
		expect(screen.getByText('Orphan Logs')).toBeInTheDocument();
		expect(screen.getByText('Orphan Folders')).toBeInTheDocument();
		expect(screen.getByText('Notifications')).toBeInTheDocument();
		expect(screen.getByText('Transcoder Jobs')).toBeInTheDocument();
	});

	it('shows summary counts after load', async () => {
		renderComponent(MaintenancePage);
		await waitFor(() => {
			expect(screen.getByText('3')).toBeInTheDocument(); // orphan logs
			expect(screen.getByText('5')).toBeInTheDocument(); // orphan folders
			expect(screen.getByText('8')).toBeInTheDocument(); // transcoder jobs
		});
	});

	it('expands orphan logs section and shows files', async () => {
		renderComponent(MaintenancePage);
		await waitFor(() => expect(screen.getByText('3')).toBeInTheDocument());

		await fireEvent.click(screen.getByText('Orphan Logs'));
		await waitFor(() => {
			expect(screen.getByText('a.log')).toBeInTheDocument();
			expect(screen.getByText('b.log')).toBeInTheDocument();
		});
	});

	it('expands orphan folders section and shows folders', async () => {
		renderComponent(MaintenancePage);
		await waitFor(() => expect(screen.getByText('5')).toBeInTheDocument());

		await fireEvent.click(screen.getByText('Orphan Folders'));
		await waitFor(() => {
			expect(screen.getByText('Orphan')).toBeInTheDocument();
			expect(screen.getByText('raw')).toBeInTheDocument();
		});
	});

	it('expands notifications section and shows action buttons', async () => {
		renderComponent(MaintenancePage);
		await waitFor(() => expect(screen.getByText('Notifications')).toBeInTheDocument());

		await fireEvent.click(screen.getByText('Notifications'));
		await waitFor(() => {
			expect(screen.getByText(/Dismiss All Unseen/)).toBeInTheDocument();
			expect(screen.getByText(/Purge Cleared/)).toBeInTheDocument();
		});
	});
});
