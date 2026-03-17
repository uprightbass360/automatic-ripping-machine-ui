import { describe, it, expect, afterEach } from 'vitest';
import { renderComponent, screen, cleanup } from '$lib/test-utils';
import StatusBadge from './StatusBadge.svelte';

describe('StatusBadge', () => {
	afterEach(() => cleanup());
	describe('rendering', () => {
		it('renders with a known status', () => {
			renderComponent(StatusBadge, { props: { status: 'ripping' } });
			const badge = screen.getByText('Ripping');
			expect(badge).toBeInTheDocument();
			expect(badge).toHaveClass('status-active');
		});

		it('renders with null status', () => {
			renderComponent(StatusBadge, { props: { status: null } });
			const badge = screen.getByText('Unknown');
			expect(badge).toBeInTheDocument();
			expect(badge).toHaveClass('status-unknown');
		});
	});

	describe('props', () => {
		it('renders unknown status string as-is with unknown class', () => {
			renderComponent(StatusBadge, { props: { status: 'something_new' } });
			const badge = screen.getByText('something_new');
			expect(badge).toBeInTheDocument();
			expect(badge).toHaveClass('status-unknown');
		});

		it('handles status case insensitively', () => {
			renderComponent(StatusBadge, { props: { status: 'SUCCESS' } });
			const badge = screen.getByText('Success');
			expect(badge).toBeInTheDocument();
			expect(badge).toHaveClass('status-success');
		});

		it('renders mapped label that differs from raw status', () => {
			renderComponent(StatusBadge, { props: { status: 'copying' } });
			const badge = screen.getByText('Copying Files');
			expect(badge).toBeInTheDocument();
			expect(badge).toHaveClass('status-warning');
		});
	});
});
