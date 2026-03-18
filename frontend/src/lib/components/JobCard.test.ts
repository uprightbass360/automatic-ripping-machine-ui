import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderComponent, screen, cleanup } from '$lib/test-utils';
import JobCard from './JobCard.svelte';
import { createJob } from './__fixtures__/job';

describe('JobCard', () => {
	beforeEach(() => {
		vi.useFakeTimers();
		vi.setSystemTime(new Date('2025-06-15T12:00:00Z'));
	});

	afterEach(() => {
		cleanup();
		vi.useRealTimers();
	});

	describe('rendering', () => {
		it('renders job title', () => {
			renderComponent(JobCard, { props: { job: createJob() } });
			expect(screen.getByText('Test Movie')).toBeInTheDocument();
		});

		it('renders Untitled when no title or label', () => {
			renderComponent(JobCard, {
				props: { job: createJob({ title: null, label: null }) }
			});
			expect(screen.getByText('Untitled')).toBeInTheDocument();
		});

		it('renders year when present', () => {
			renderComponent(JobCard, { props: { job: createJob() } });
			expect(screen.getByText('2024')).toBeInTheDocument();
		});

		it('renders status badge', () => {
			renderComponent(JobCard, { props: { job: createJob({ status: 'success' }) } });
			expect(screen.getByText('Success')).toBeInTheDocument();
		});

		it('renders disc label when it differs from title', () => {
			renderComponent(JobCard, {
				props: { job: createJob({ title: 'My Movie', label: 'DIFFERENT_LABEL' }) }
			});
			expect(screen.getByText('DIFFERENT_LABEL')).toBeInTheDocument();
		});

		it('does not render disc label when same as title', () => {
			renderComponent(JobCard, {
				props: { job: createJob({ title: 'Test Movie', label: 'test movie' }) }
			});
			// label should not appear separately since it matches title (case-insensitive)
			const labels = screen.queryAllByText(/test movie/i);
			// Only the title should appear, not a separate label element
			expect(labels.length).toBe(1);
		});
	});

	describe('props', () => {
		it('renders IMDb button when imdb_id is present', () => {
			renderComponent(JobCard, {
				props: { job: createJob({ imdb_id: 'tt1234567' }) }
			});
			expect(screen.getByText('IMDb')).toBeInTheDocument();
		});

		it('does not render IMDb button when no imdb_id', () => {
			renderComponent(JobCard, { props: { job: createJob() } });
			expect(screen.queryByText('IMDb')).not.toBeInTheDocument();
		});

		it('shows stage for active jobs', () => {
			renderComponent(JobCard, {
				props: { job: createJob({ status: 'ripping', stage: 'Ripping track 2' }) }
			});
			expect(screen.getByText('Ripping track 2')).toBeInTheDocument();
		});

		it('renders drive name from driveNames map', () => {
			renderComponent(JobCard, {
				props: {
					job: createJob({ devpath: '/dev/sr0' }),
					driveNames: { '/dev/sr0': 'Main Drive' }
				}
			});
			expect(screen.getByText('Main Drive')).toBeInTheDocument();
		});

		it('shows progress bar when progress is provided', () => {
			const { container } = renderComponent(JobCard, {
				props: { job: createJob(), progress: 50 }
			});
			expect(container.querySelector('[data-progress-track]')).toBeInTheDocument();
		});

		it('shows indeterminate bar when active with no progress', () => {
			const { container } = renderComponent(JobCard, {
				props: { job: createJob({ status: 'ripping' }) }
			});
			expect(container.querySelector('.animate-indeterminate')).toBeInTheDocument();
		});

		it('shows errors indicator when job has errors', () => {
			renderComponent(JobCard, {
				props: { job: createJob({ errors: 'Something went wrong' }) }
			});
			expect(screen.getByText('errors')).toBeInTheDocument();
		});
	});
});
