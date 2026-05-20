import { describe, it, expect, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup } from '$lib/test-utils';
import ChannelCard from '../ChannelCard.svelte';
import type { Channel } from '$lib/types/notifications';

function chan(over: Partial<Channel> = {}): Channel {
	return {
		id: 1, type: 'apprise', name: 'Family Discord', enabled: true,
		config: { type: 'apprise', url: 'discord://a/b' },
		subscribed_events: ['job.started', 'job.failed'],
		templates: {}, last_fired_at: null, last_success_at: null, last_error: null,
		...over
	} as Channel;
}

describe('ChannelCard', () => {
	afterEach(() => cleanup());

	it('shows the channel name and type', () => {
		renderComponent(ChannelCard, { props: { channel: chan(), ontest: () => {}, ondelete: () => {} } });
		expect(screen.getByText('Family Discord')).toBeTruthy();
		expect(screen.getByText(/apprise/)).toBeTruthy();
	});

	it('shows a healthy status dot when enabled and no error', () => {
		const { container } = renderComponent(ChannelCard, { props: { channel: chan(), ontest: () => {}, ondelete: () => {} } });
		expect(container.querySelector('.status-dot--healthy')).toBeTruthy();
	});

	it('shows an error status dot when last_error is set', () => {
		const { container } = renderComponent(ChannelCard, { props: { channel: chan({ last_error: 'http 503' }), ontest: () => {}, ondelete: () => {} } });
		expect(container.querySelector('.status-dot--error')).toBeTruthy();
	});

	it('shows a disabled status dot when not enabled', () => {
		const { container } = renderComponent(ChannelCard, { props: { channel: chan({ enabled: false }), ontest: () => {}, ondelete: () => {} } });
		expect(container.querySelector('.status-dot--disabled')).toBeTruthy();
	});

	it('calls ontest when Test is clicked', async () => {
		let tested = 0;
		renderComponent(ChannelCard, { props: { channel: chan(), ontest: () => (tested = 1), ondelete: () => {} } });
		await fireEvent.click(screen.getByText('Test'));
		expect(tested).toBe(1);
	});
});
