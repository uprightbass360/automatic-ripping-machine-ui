import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup, waitFor } from '$lib/test-utils';
import LogsPage from '../+page.svelte';

vi.mock('$lib/api/logs', () => ({
	fetchLogs: vi.fn(() => Promise.resolve([
		{ filename: 'job_001.log', size: 1024, modified: '2025-06-15T12:00:00Z' },
		{ filename: 'job_002.log', size: 2048, modified: '2025-06-14T10:00:00Z' }
	])),
	fetchTranscoderLogs: vi.fn(() => Promise.resolve([
		{ filename: 'transcode_001.log', size: 512, modified: '2025-06-15T11:00:00Z' }
	]))
}));

describe('Logs Page', () => {
	afterEach(() => cleanup());

	describe('rendering', () => {
		it('renders page title', async () => {
			renderComponent(LogsPage);
			expect(screen.getByText('Log Files')).toBeInTheDocument();
		});

		it('renders ARM and Transcoder tabs', () => {
			renderComponent(LogsPage);
			expect(screen.getByText('ARM Ripper')).toBeInTheDocument();
			expect(screen.getByText('Transcoder')).toBeInTheDocument();
		});

		it('renders ARM log files after loading', async () => {
			renderComponent(LogsPage);
			await waitFor(() => {
				expect(screen.getByText('job_001.log')).toBeInTheDocument();
				expect(screen.getByText('job_002.log')).toBeInTheDocument();
			});
		});

		it('renders log file links to /logs/:filename', async () => {
			renderComponent(LogsPage);
			await waitFor(() => {
				const link = screen.getByText('job_001.log');
				expect(link.closest('a')).toHaveAttribute('href', '/logs/job_001.log');
			});
		});

		it('renders sortable column headers', async () => {
			renderComponent(LogsPage);
			await waitFor(() => {
				expect(screen.getByText('Filename')).toBeInTheDocument();
				expect(screen.getByText('Size')).toBeInTheDocument();
				expect(screen.getByText('Last Modified')).toBeInTheDocument();
			});
		});
	});

	describe('interactions', () => {
		it('switches to transcoder tab', async () => {
			renderComponent(LogsPage);
			await waitFor(() => {
				expect(screen.getByText('job_001.log')).toBeInTheDocument();
			});
			await fireEvent.click(screen.getByText('Transcoder'));
			await waitFor(() => {
				expect(screen.getByText('transcode_001.log')).toBeInTheDocument();
			});
		});
	});
});
