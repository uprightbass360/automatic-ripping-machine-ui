import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, waitFor, cleanup } from '$lib/test-utils';
import ChannelEditor from '../ChannelEditor.svelte';
import type { Channel, Catalog } from '$lib/types/notifications';
import { discordCatalog, appriseChannel, webhookChannel } from './apprise-fixtures';

const catalog: Catalog = { featured: [], services: [] };
const ch: Channel = webhookChannel({ id: 3 });

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

	it('apprise editor renders the service fields resolved from service_id', async () => {
		const catalog = discordCatalog;
		const ch = appriseChannel({ id: 7 });
		renderComponent(ChannelEditor, { props: { channel: ch, catalog, onsave: () => {}, ontest: () => {}, onclose: () => {}, ondelete: () => {} } });
		const wid = await screen.findByLabelText(/Webhook ID/i) as HTMLInputElement;
		expect(wid).toBeInTheDocument();
		expect(wid.value).toBe('');
	});

	it('apprise editor save with blank fields reports empty appriseFields (keep current)', async () => {
		const onsave = vi.fn();
		const catalog = discordCatalog;
		const ch = appriseChannel({ id: 7 });
		renderComponent(ChannelEditor, { props: { channel: ch, catalog, onsave, ontest: () => {}, onclose: () => {}, ondelete: () => {} } });
		await fireEvent.input(screen.getByLabelText('Channel Label'), { target: { value: 'D2' } });
		await waitFor(() => expect(screen.getByRole('button', { name: /save changes/i })).toBeEnabled());
		await fireEvent.click(screen.getByRole('button', { name: /save changes/i }));
		expect(onsave).toHaveBeenCalledWith(expect.objectContaining({ name: 'D2', serviceId: 'discord' }));
		const arg = onsave.mock.calls[0][0];
		expect(Object.values(arg.appriseFields).filter((v) => v && String(v).trim() !== '')).toEqual([]);
	});

	it('apprise editor save with filled fields reports them in appriseFields', async () => {
		const onsave = vi.fn();
		const catalog = discordCatalog;
		const ch = appriseChannel({ id: 7 });
		renderComponent(ChannelEditor, { props: { channel: ch, catalog, onsave, ontest: () => {}, onclose: () => {}, ondelete: () => {} } });
		await fireEvent.input(await screen.findByLabelText(/Webhook ID/i), { target: { value: '99' } });
		await waitFor(() => expect(screen.getByRole('button', { name: /save changes/i })).toBeEnabled());
		await fireEvent.click(screen.getByRole('button', { name: /save changes/i }));
		expect(onsave.mock.calls[0][0].appriseFields).toEqual(expect.objectContaining({ webhook_id: '99' }));
	});

	it('shows a notice when service_id is not in the catalog', async () => {
		const catalog = { featured: [], services: [] };  // discord absent
		const ch = appriseChannel({ id: 7 });
		renderComponent(ChannelEditor, { props: { channel: ch, catalog, onsave: () => {}, ontest: () => {}, onclose: () => {}, ondelete: () => {} } });
		expect(await screen.findByText(/Unknown service 'discord'/i)).toBeInTheDocument();
	});
});
