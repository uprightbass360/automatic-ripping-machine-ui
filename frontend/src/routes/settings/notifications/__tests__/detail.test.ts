import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, waitFor, cleanup } from '$lib/test-utils';
import Page from '../[id]/+page.svelte';
import * as channelsApi from '$lib/api/channels';

vi.mock('$lib/api/channels');
vi.mock('$app/navigation', () => ({ goto: vi.fn(), invalidateAll: vi.fn() }));

function data() {
	return {
		channel: {
			id: 5, type: 'apprise', name: 'Discord', enabled: true,
			config: { type: 'apprise', url: 'discord://a/b' },
			subscribed_events: ['job.started'], templates: {},
			last_fired_at: null, last_success_at: null, last_error: null
		},
		dispatches: [
			{ id: 1, channel_id: 5, event_key: 'job.started', status: 'success', attempts: 1, last_error: null, created_at: '2026-05-20T00:00:00Z', completed_at: '2026-05-20T00:00:01Z' }
		]
	};
}

describe('Channel edit page', () => {
	beforeEach(() => vi.resetAllMocks());
	afterEach(() => cleanup());

	it('prefills the channel name', () => {
		renderComponent(Page, { props: { data: data() } });
		expect((screen.getByLabelText('Channel name') as HTMLInputElement).value).toBe('Discord');
	});

	it('shows dispatch history', () => {
		renderComponent(Page, { props: { data: data() } });
		expect(screen.getByText('job.started')).toBeTruthy();
	});

	it('saves changes via updateChannel', async () => {
		vi.mocked(channelsApi.updateChannel).mockResolvedValue({ id: 5 } as never);
		renderComponent(Page, { props: { data: data() } });
		await fireEvent.input(screen.getByLabelText('Channel name'), { target: { value: 'Renamed' } });
		await fireEvent.click(screen.getByText('Save'));
		expect(channelsApi.updateChannel).toHaveBeenCalledWith(5, expect.objectContaining({ name: 'Renamed' }));
	});

	it('test-send polls dispatch status to success', async () => {
		vi.mocked(channelsApi.testSendChannel).mockResolvedValue({ sent_at: 'now', dispatch_id: 9 });
		vi.mocked(channelsApi.fetchDispatch).mockResolvedValue({ id: 9, status: 'success', attempts: 1, last_error: null, completed_at: 'now' });
		renderComponent(Page, { props: { data: data() } });
		await fireEvent.click(screen.getByText('Test'));
		await waitFor(() => expect(screen.getByText(/Test sent successfully/i)).toBeTruthy(), { timeout: 3000 });
	});
});
