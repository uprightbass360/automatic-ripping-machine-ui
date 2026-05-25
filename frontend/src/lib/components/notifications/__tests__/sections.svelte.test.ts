import { describe, it, expect, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup } from '$lib/test-utils';
import EventsSection from '../sections/EventsSection.svelte';
import ConfigureSection from '../sections/ConfigureSection.svelte';

describe('EventsSection', () => {
	afterEach(() => cleanup());

	it('select all checks every event; clear empties them', async () => {
		const props = $state({ selected: [] as string[] });
		renderComponent(EventsSection, { props });
		await fireEvent.click(screen.getByRole('button', { name: /select all/i }));
		expect(props.selected.length).toBe(6);
		await fireEvent.click(screen.getByRole('button', { name: /clear/i }));
		expect(props.selected.length).toBe(0);
	});
});

describe('ConfigureSection', () => {
	afterEach(() => cleanup());

	it('renders the channel label input and enabled toggle', () => {
		const props = $state({
			type: 'webhook' as const, name: '', enabled: true,
			config: {} as Record<string, unknown>, service: null
		});
		renderComponent(ConfigureSection, { props });
		expect(screen.getByLabelText(/channel label/i)).toBeInTheDocument();
		expect(screen.getByRole('switch', { name: /enabled/i })).toBeInTheDocument();
	});

	it('renders webhook fields (URL) for webhook type', () => {
		const props = $state({
			type: 'webhook' as const, name: '', enabled: true,
			config: {} as Record<string, unknown>, service: null
		});
		renderComponent(ConfigureSection, { props });
		expect(screen.getByLabelText(/webhook url/i)).toBeInTheDocument();
	});

	it('preserveExisting makes config fields optional and shows the keep-current hint', () => {
		const props = $state({
			type: 'webhook' as const, name: 'x', enabled: true,
			config: {} as Record<string, unknown>, service: null, preserveExisting: true
		});
		renderComponent(ConfigureSection, { props });
		const url = screen.getByLabelText(/webhook url/i) as HTMLInputElement;
		expect(url.required).toBe(false);
		expect(screen.getByText(/leave blank to keep/i)).toBeInTheDocument();
	});

	it('without preserveExisting, required fields stay required', () => {
		const props = $state({
			type: 'webhook' as const, name: 'x', enabled: true,
			config: {} as Record<string, unknown>, service: null
		});
		renderComponent(ConfigureSection, { props });
		const url = screen.getByLabelText(/webhook url/i) as HTMLInputElement;
		expect(url.required).toBe(true);
	});
});
