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

	it('shows a closed dropdown trigger by default', () => {
		renderComponent(ServicePicker, { props: { catalog, onpick: () => {} } });
		const trigger = screen.getByRole('button', { name: /select a service/i });
		expect(trigger).toBeTruthy();
		expect(trigger.getAttribute('aria-expanded')).toBe('false');
		// Options are not rendered until opened.
		expect(screen.queryByText('Discord')).toBeNull();
	});

	it('reveals all services when opened, featured first', async () => {
		renderComponent(ServicePicker, { props: { catalog, onpick: () => {} } });
		await fireEvent.click(screen.getByRole('button', { name: /select a service/i }));
		// Featured services...
		expect(screen.getByText('Discord')).toBeTruthy();
		expect(screen.getByText('Slack')).toBeTruthy();
		// ...and non-featured services are all shown by default now.
		expect(screen.getByText('Telegram')).toBeTruthy();
	});

	it('filters across all services by search substring', async () => {
		renderComponent(ServicePicker, { props: { catalog, onpick: () => {} } });
		await fireEvent.click(screen.getByRole('button', { name: /select a service/i }));
		await fireEvent.input(screen.getByPlaceholderText('Search services'), { target: { value: 'tele' } });
		expect(screen.queryByText('Telegram')).toBeTruthy();
		expect(screen.queryByText('Discord')).toBeNull();
	});

	it('calls onpick with the service id and closes', async () => {
		let picked = '';
		renderComponent(ServicePicker, { props: { catalog, onpick: (id: string) => (picked = id) } });
		await fireEvent.click(screen.getByRole('button', { name: /select a service/i }));
		await fireEvent.click(screen.getByText('Discord'));
		expect(picked).toBe('discord');
		// Dropdown closed after selection.
		expect(screen.queryByText('Slack')).toBeNull();
	});

	it('shows an empty state when nothing matches', async () => {
		renderComponent(ServicePicker, { props: { catalog, onpick: () => {} } });
		await fireEvent.click(screen.getByRole('button', { name: /select a service/i }));
		await fireEvent.input(screen.getByPlaceholderText('Search services'), { target: { value: 'zzz' } });
		expect(screen.getByText(/No services match/i)).toBeTruthy();
	});
});
