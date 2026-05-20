import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup } from '$lib/test-utils';
import Page from '../new/+page.svelte';
import * as channelsApi from '$lib/api/channels';

vi.mock('$lib/api/channels');
vi.mock('$app/navigation', () => ({ goto: vi.fn() }));

const catalog = {
	featured: ['discord'],
	services: [
		{
			id: 'discord', name: 'Discord', docs_url: '', url_scheme: 'discord',
			required_fields: [{ key: 'webhook_id', label: 'Webhook ID', type: 'string', private: true, required: true }],
			advanced_fields: []
		}
	]
};

describe('Create channel flow', () => {
	beforeEach(() => vi.resetAllMocks());
	afterEach(() => cleanup());

	it('starts on the type-picker step', () => {
		renderComponent(Page, { props: { data: { catalog } } });
		expect(screen.getByText(/Choose channel type/i)).toBeTruthy();
	});

	it('webhook type shows URL + secret fields after Next', async () => {
		renderComponent(Page, { props: { data: { catalog } } });
		await fireEvent.click(screen.getByLabelText('Webhook'));
		await fireEvent.click(screen.getByText('Next'));
		expect(screen.getByLabelText(/Webhook URL/i)).toBeTruthy();
		expect(screen.getByLabelText(/Shared secret/i)).toBeTruthy();
	});

	it('bash type shows script path field after Next', async () => {
		renderComponent(Page, { props: { data: { catalog } } });
		await fireEvent.click(screen.getByLabelText('Bash script'));
		await fireEvent.click(screen.getByText('Next'));
		expect(screen.getByLabelText(/Script path/i)).toBeTruthy();
	});

	it('apprise webhook save composes URL then creates the channel', async () => {
		vi.mocked(channelsApi.composeUrl).mockResolvedValue({ url: 'discord://wid' });
		vi.mocked(channelsApi.createChannel).mockResolvedValue({ id: 7 } as never);

		renderComponent(Page, { props: { data: { catalog } } });
		// type = apprise (default) -> Next
		await fireEvent.click(screen.getByText('Next'));
		// pick discord
		await fireEvent.click(screen.getByText('Discord'));
		// fill required field
		await fireEvent.input(screen.getByLabelText('Webhook ID'), { target: { value: 'wid' } });
		// name
		await fireEvent.input(screen.getByLabelText('Channel name'), { target: { value: 'My Discord' } });
		// save
		await fireEvent.click(screen.getByText('Save'));

		expect(channelsApi.composeUrl).toHaveBeenCalledWith('discord', { webhook_id: 'wid' }, {});
		expect(channelsApi.createChannel).toHaveBeenCalledWith(
			expect.objectContaining({
				type: 'apprise',
				name: 'My Discord',
				config: { type: 'apprise', url: 'discord://wid' }
			})
		);
	});
});
