import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, waitFor, cleanup } from '$lib/test-utils';
import ChannelEditor from '../ChannelEditor.svelte';
import type { Channel, Catalog } from '$lib/types/notifications';

const catalog: Catalog = { featured: [], services: [] };
const ch: Channel = {
	id: 3, type: 'webhook', name: 'Hook', enabled: true,
	config: { type: 'webhook', url: 'https://x' },
	subscribed_events: ['job.started'], templates: {},
	last_fired_at: null, last_success_at: null, last_error: null
};

describe('ChannelEditor', () => {
	afterEach(() => cleanup());

	it('Save changes is disabled until a field changes', async () => {
		renderComponent(ChannelEditor, { props: { channel: ch, catalog, onsave: () => {}, ontest: () => {}, onclose: () => {}, ondelete: () => {} } });
		expect(screen.getByRole('button', { name: /save changes/i })).toBeDisabled();
		await fireEvent.input(screen.getByLabelText('Channel Label'), { target: { value: 'Hook 2' } });
		await waitFor(() => expect(screen.getByRole('button', { name: /save changes/i })).toBeEnabled());
	});

	it('Delete fires ondelete', async () => {
		const ondelete = vi.fn();
		renderComponent(ChannelEditor, { props: { channel: ch, catalog, onsave: () => {}, ontest: () => {}, onclose: () => {}, ondelete } });
		await fireEvent.click(screen.getByRole('button', { name: /delete/i }));
		expect(ondelete).toHaveBeenCalled();
	});
});
