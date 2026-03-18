import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup, waitFor } from '$lib/test-utils';
import NotificationsPage from '../+page.svelte';

vi.mock('$lib/api/notifications', () => ({
	fetchNotifications: vi.fn(() => Promise.resolve([
		{ id: 1, title: 'Job Complete', message: 'Movie ripped successfully', seen: false, trigger_time: '2025-06-15T12:00:00Z' },
		{ id: 2, title: 'Error', message: 'Rip failed', seen: true, trigger_time: '2025-06-14T10:00:00Z' }
	])),
	dismissNotification: vi.fn(() => Promise.resolve({}))
}));

describe('Notifications Page', () => {
	afterEach(() => cleanup());

	describe('rendering', () => {
		it('renders page title', () => {
			renderComponent(NotificationsPage);
			expect(screen.getByText('Notifications')).toBeInTheDocument();
		});

		it('shows unseen notification count', async () => {
			renderComponent(NotificationsPage);
			await waitFor(() => {
				expect(screen.getByText('1 new')).toBeInTheDocument();
			});
		});

		it('renders unseen notifications by default', async () => {
			renderComponent(NotificationsPage);
			await waitFor(() => {
				expect(screen.getByText('Job Complete')).toBeInTheDocument();
				// Seen notification should be hidden by default
				expect(screen.queryByText('Error')).not.toBeInTheDocument();
			});
		});

		it('shows Dismiss All button for unseen notifications', async () => {
			renderComponent(NotificationsPage);
			await waitFor(() => {
				expect(screen.getByText('Dismiss All')).toBeInTheDocument();
			});
		});

		it('shows Show dismissed checkbox', () => {
			renderComponent(NotificationsPage);
			expect(screen.getByText('Show dismissed')).toBeInTheDocument();
		});
	});

	describe('interactions', () => {
		it('shows dismissed notifications when checkbox toggled', async () => {
			renderComponent(NotificationsPage);
			await waitFor(() => {
				expect(screen.getByText('Job Complete')).toBeInTheDocument();
			});
			const checkbox = screen.getByRole('checkbox');
			await fireEvent.click(checkbox);
			await waitFor(() => {
				expect(screen.getByText('Error')).toBeInTheDocument();
			});
		});

		it('renders dismiss button for unseen notifications', async () => {
			renderComponent(NotificationsPage);
			await waitFor(() => {
				expect(screen.getByText('Dismiss')).toBeInTheDocument();
			});
		});
	});
});
