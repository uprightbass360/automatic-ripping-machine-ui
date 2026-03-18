import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup, waitFor } from '$lib/test-utils';
import InlineLogFeed from './InlineLogFeed.svelte';

const mockEntries = [
	{ level: 'error', event: 'Something failed', timestamp: '2025-06-15T12:00:01Z' },
	{ level: 'warning', event: 'Disk space low', timestamp: '2025-06-15T12:00:02Z' },
	{ level: 'info', event: 'Job started', timestamp: '2025-06-15T12:00:03Z' }
];

function createFetchFn(entries = mockEntries) {
	return vi.fn(() => Promise.resolve({ entries }));
}

describe('InlineLogFeed', () => {
	afterEach(() => cleanup());

	describe('rendering', () => {
		it('renders title and entry count after loading', async () => {
			renderComponent(InlineLogFeed, {
				props: { logfile: 'test.log', fetchFn: createFetchFn(), autoRefresh: false }
			});
			await waitFor(() => {
				expect(screen.getByText('Recent Log')).toBeInTheDocument();
				expect(screen.getByText('3 entries')).toBeInTheDocument();
			});
		});

		it('renders custom title', async () => {
			renderComponent(InlineLogFeed, {
				props: { logfile: 'test.log', fetchFn: createFetchFn(), autoRefresh: false, title: 'Job Log' }
			});
			await waitFor(() => {
				expect(screen.getByText('Job Log')).toBeInTheDocument();
			});
		});

		it('shows error count badge', async () => {
			renderComponent(InlineLogFeed, {
				props: { logfile: 'test.log', fetchFn: createFetchFn(), autoRefresh: false }
			});
			await waitFor(() => {
				expect(screen.getByText('1 error')).toBeInTheDocument();
			});
		});

		it('shows warning count badge', async () => {
			renderComponent(InlineLogFeed, {
				props: { logfile: 'test.log', fetchFn: createFetchFn(), autoRefresh: false }
			});
			await waitFor(() => {
				expect(screen.getByText('1 warning')).toBeInTheDocument();
			});
		});

		it('renders nothing when entries are empty', async () => {
			const { container } = renderComponent(InlineLogFeed, {
				props: { logfile: 'test.log', fetchFn: createFetchFn([]), autoRefresh: false }
			});
			await waitFor(() => {
				expect(container.querySelector('.rounded-lg')).toBeNull();
			});
		});

		it('shows error message on fetch failure', async () => {
			const fetchFn = vi.fn(() => Promise.reject(new Error('Failed')));
			renderComponent(InlineLogFeed, {
				props: { logfile: 'test.log', fetchFn, autoRefresh: false }
			});
			await waitFor(() => {
				expect(screen.getByText('Failed')).toBeInTheDocument();
			});
		});
	});

	describe('interactions', () => {
		it('expands to show log entries when clicked', async () => {
			renderComponent(InlineLogFeed, {
				props: { logfile: 'test.log', fetchFn: createFetchFn(), autoRefresh: false }
			});
			await waitFor(() => {
				expect(screen.getByText('Recent Log')).toBeInTheDocument();
			});
			await fireEvent.click(screen.getByText('Recent Log'));
			expect(screen.getByText('Something failed')).toBeInTheDocument();
			expect(screen.getByText('Disk space low')).toBeInTheDocument();
		});

		it('shows view full log link when expanded', async () => {
			renderComponent(InlineLogFeed, {
				props: { logfile: 'test.log', fetchFn: createFetchFn(), autoRefresh: false }
			});
			await waitFor(() => {
				expect(screen.getByText('Recent Log')).toBeInTheDocument();
			});
			await fireEvent.click(screen.getByText('Recent Log'));
			const link = screen.getByText(/View full log/);
			expect(link.closest('a')).toHaveAttribute('href', '/logs/test.log');
		});
	});
});
