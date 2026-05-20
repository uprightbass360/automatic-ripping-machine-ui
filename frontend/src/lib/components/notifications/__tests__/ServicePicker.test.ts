import { describe, it, expect, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup } from '$lib/test-utils';
import ServicePicker from '../ServicePicker.svelte';
import type { Catalog } from '$lib/types/notifications';

const catalog: Catalog = {
	featured: ['discord', 'slack'],
	services: [
		{ id: 'discord', name: 'Discord', docs_url: '', url_scheme: 'discord', required_fields: [], advanced_fields: [] },
		{ id: 'slack', name: 'Slack', docs_url: '', url_scheme: 'slack', required_fields: [], advanced_fields: [] },
		{ id: 'telegram', name: 'Telegram', docs_url: '', url_scheme: 'tgram', required_fields: [], advanced_fields: [] }
	]
};

describe('ServicePicker', () => {
	afterEach(() => cleanup());

	it('renders featured services', () => {
		renderComponent(ServicePicker, { props: { catalog, onpick: () => {} } });
		expect(screen.getByText('Discord')).toBeTruthy();
		expect(screen.getByText('Slack')).toBeTruthy();
	});

	it('filters by search substring', async () => {
		renderComponent(ServicePicker, { props: { catalog, onpick: () => {} } });
		await fireEvent.input(screen.getByPlaceholderText('Search services'), { target: { value: 'tele' } });
		expect(screen.queryByText('Telegram')).toBeTruthy();
		expect(screen.queryByText('Discord')).toBeNull();
	});

	it('calls onpick with the service id', async () => {
		let picked = '';
		renderComponent(ServicePicker, { props: { catalog, onpick: (id: string) => (picked = id) } });
		await fireEvent.click(screen.getByText('Discord'));
		expect(picked).toBe('discord');
	});
});
