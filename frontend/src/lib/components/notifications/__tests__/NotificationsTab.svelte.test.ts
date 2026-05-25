import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, waitFor, cleanup, within } from '$lib/test-utils';
import NotificationsTab from '../NotificationsTab.svelte';
import * as api from '$lib/api/channels';
import { toasts, dismissToast } from '$lib/stores/toast.svelte';
import type { Channel } from '$lib/types/notifications';

const ch: Channel = {
	id: 1, type: 'webhook', name: 'Hook', enabled: true,
	config: { type: 'webhook', url: 'https://x' },
	subscribed_events: ['job.started'], templates: {},
	last_fired_at: null, last_success_at: null, last_error: null
};

describe('NotificationsTab', () => {
	beforeEach(() => {
		vi.spyOn(api, 'fetchChannels').mockResolvedValue([ch]);
		vi.spyOn(api, 'fetchServices').mockResolvedValue({ featured: [], services: [] });
	});
	afterEach(() => {
		for (const t of toasts.value) dismissToast(t.id);
		vi.restoreAllMocks();
		cleanup();
	});

	it('loads and lists channels', async () => {
		renderComponent(NotificationsTab);
		expect(await screen.findByText('Hook')).toBeInTheDocument();
	});

	it('shows the stat strip counts', async () => {
		renderComponent(NotificationsTab);
		await screen.findByText('Hook');
		const channelsLabel = screen.getByText('Channels');
		expect(channelsLabel).toBeInTheDocument();
		const card = channelsLabel.parentElement as HTMLElement;
		expect(within(card).getByText('1')).toBeInTheDocument();
	});

	it('toggle calls updateChannel and reverts on error', async () => {
		vi.spyOn(api, 'updateChannel').mockRejectedValueOnce(new Error('nope'));
		renderComponent(NotificationsTab);
		await screen.findByText('Hook');
		await fireEvent.click(screen.getByRole('switch', { name: /enabled/i }));
		await waitFor(() => expect(api.updateChannel).toHaveBeenCalledWith(1, { enabled: false }));
		await waitFor(() => expect(screen.getByRole('switch', { name: /enabled/i }).getAttribute('aria-checked')).toBe('true'));
	});
});
