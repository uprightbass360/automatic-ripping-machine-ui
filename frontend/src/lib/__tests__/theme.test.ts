import { describe, it, expect, vi } from 'vitest';
import { get } from 'svelte/store';

vi.mock('$app/environment', () => ({ browser: false }));

import { theme, toggleTheme } from '../stores/theme';

describe('theme store', () => {
	it('initial value is dark when browser is false', () => {
		expect(get(theme)).toBe('dark');
	});

	it('toggleTheme flips dark to light', () => {
		theme.set('dark');
		toggleTheme();
		expect(get(theme)).toBe('light');
	});

	it('toggleTheme flips light to dark', () => {
		theme.set('light');
		toggleTheme();
		expect(get(theme)).toBe('dark');
	});

	it('toggleTheme round-trips correctly', () => {
		theme.set('dark');
		toggleTheme();
		toggleTheme();
		expect(get(theme)).toBe('dark');
	});
});
