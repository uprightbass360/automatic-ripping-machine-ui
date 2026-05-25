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

	it('test-send polls until the dispatch reaches a terminal status', async () => {
		vi.useFakeTimers();
		vi.spyOn(api, 'testSendChannel').mockResolvedValue({ sent_at: 'now', dispatch_id: 9 });
		const fetchDispatch = vi.spyOn(api, 'fetchDispatch')
			.mockResolvedValueOnce({ id: 9, status: 'in_flight', attempts: 1, last_error: null, completed_at: null })
			.mockResolvedValueOnce({ id: 9, status: 'success', attempts: 1, last_error: null, completed_at: 'now' });

		renderComponent(NotificationsTab);
		// loaded state — advance microtasks; channels resolve
		await vi.advanceTimersByTimeAsync(0);
		// Click the row's Send test button (aria-label "Send test")
		await fireEvent.click(screen.getByRole('button', { name: /send test/i }));
		// Advance through two 500ms poll iterations
		await vi.advanceTimersByTimeAsync(1100);

		expect(fetchDispatch).toHaveBeenCalledTimes(2);
		expect(toasts.value.some((t) => t.title === 'Test delivered')).toBe(true);
		expect(toasts.value.some((t) => t.title === 'Test failed')).toBe(false);
		vi.useRealTimers();
	});

	it('editor Send test uses testConfig with the edited body, not testSendChannel', async () => {
		const testConfig = vi.spyOn(api, 'testConfig').mockResolvedValue({ ok: true, error: null });
		const testSend = vi.spyOn(api, 'testSendChannel');
		renderComponent(NotificationsTab);
		await screen.findByText('Hook');
		// Expand the row (click the channel name / row, not the toggle or actions)
		await fireEvent.click(screen.getByText('Hook'));
		// The collapsed row's test button uses an icon with aria-label "Send test";
		// the editor's uses visible text "Send test". Filter by visible textContent
		// to reliably target the editor's button.
		const sendTestButtons = await screen.findAllByRole('button', { name: /send test/i });
		const editorBtn = sendTestButtons.find((b) => b.textContent?.toLowerCase().includes('send test'));
		await fireEvent.click(editorBtn!);
		await waitFor(() => expect(testConfig).toHaveBeenCalledWith(
			expect.objectContaining({ type: 'webhook', config: expect.objectContaining({ url: 'https://x' }) })
		));
		expect(testSend).not.toHaveBeenCalled();
	});
});
