import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderComponent, screen, cleanup } from '$lib/test-utils';
import Page from '../+page.svelte';

vi.mock('$lib/api/channels');
vi.mock('$app/navigation', () => ({ goto: vi.fn(), invalidateAll: vi.fn() }));

describe('Notifications list page', () => {
	beforeEach(() => vi.resetAllMocks());
	afterEach(() => cleanup());

	it('renders a card per channel from data', () => {
		const data = {
			channels: [
				{ id: 1, type: 'apprise', name: 'Discord', enabled: true, config: { type: 'apprise', url: 'd://a/b' }, subscribed_events: ['job.started'], templates: {}, last_fired_at: null, last_success_at: null, last_error: null },
				{ id: 2, type: 'webhook', name: 'HA', enabled: true, config: { type: 'webhook', url: 'https://x', shared_secret: '<hidden>' }, subscribed_events: ['job.failed'], templates: {}, last_fired_at: null, last_success_at: null, last_error: null }
			]
		};
		renderComponent(Page, { props: { data } });
		expect(screen.getByText('Discord')).toBeTruthy();
		expect(screen.getByText('HA')).toBeTruthy();
	});

	it('renders an empty state with an add link when there are no channels', () => {
		renderComponent(Page, { props: { data: { channels: [] } } });
		expect(screen.getByText(/No notification channels/i)).toBeTruthy();
		expect(screen.getByText('Add channel')).toBeTruthy();
	});
});
