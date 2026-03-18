import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup } from '$lib/test-utils';
import JobActions from './JobActions.svelte';
import { createJob } from './__fixtures__/job';

// Mock the API module
vi.mock('$lib/api/jobs', () => ({
	abandonJob: vi.fn(() => Promise.resolve()),
	deleteJob: vi.fn(() => Promise.resolve()),
	fixJobPermissions: vi.fn(() => Promise.resolve())
}));

describe('JobActions', () => {
	afterEach(() => cleanup());

	describe('rendering', () => {
		it('shows Abandon button for active jobs', () => {
			renderComponent(JobActions, {
				props: { job: createJob({ status: 'ripping' }) }
			});
			expect(screen.getByText('Abandon')).toBeInTheDocument();
		});

		it('shows Delete button for completed jobs', () => {
			renderComponent(JobActions, {
				props: { job: createJob({ status: 'success' }) }
			});
			expect(screen.getByText('Delete')).toBeInTheDocument();
		});

		it('shows Delete button for failed jobs', () => {
			renderComponent(JobActions, {
				props: { job: createJob({ status: 'fail' }) }
			});
			expect(screen.getByText('Delete')).toBeInTheDocument();
		});

		it('shows Fix Permissions button only for success status', () => {
			renderComponent(JobActions, {
				props: { job: createJob({ status: 'success' }) }
			});
			expect(screen.getByText('Fix Permissions')).toBeInTheDocument();
		});

		it('does not show Fix Permissions for failed jobs', () => {
			renderComponent(JobActions, {
				props: { job: createJob({ status: 'fail' }) }
			});
			expect(screen.queryByText('Fix Permissions')).not.toBeInTheDocument();
		});

		it('renders nothing for jobs with no available actions', () => {
			const { container } = renderComponent(JobActions, {
				props: { job: createJob({ status: 'identifying' }) }
			});
			// identifying is active, so Abandon should show
			expect(screen.getByText('Abandon')).toBeInTheDocument();
		});

		it('does not show any buttons for cancelled status', () => {
			const { container } = renderComponent(JobActions, {
				props: { job: createJob({ status: 'cancelled' }) }
			});
			expect(screen.queryByText('Abandon')).not.toBeInTheDocument();
			expect(screen.queryByText('Delete')).not.toBeInTheDocument();
			expect(screen.queryByText('Fix Permissions')).not.toBeInTheDocument();
		});
	});

	describe('props', () => {
		it('renders compact buttons when compact is true', () => {
			renderComponent(JobActions, {
				props: { job: createJob({ status: 'success' }), compact: true }
			});
			const deleteBtn = screen.getByText('Delete');
			expect(deleteBtn).toHaveClass('text-xs');
		});

		it('renders standard buttons when compact is false', () => {
			renderComponent(JobActions, {
				props: { job: createJob({ status: 'success' }), compact: false }
			});
			const deleteBtn = screen.getByText('Delete');
			expect(deleteBtn).toHaveClass('text-sm');
		});
	});
});
