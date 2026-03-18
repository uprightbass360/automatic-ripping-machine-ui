import { describe, it, expect, afterEach } from 'vitest';
import { renderComponent, cleanup } from '$lib/test-utils';
import FileIcon from './FileIcon.svelte';

describe('FileIcon', () => {
	afterEach(() => cleanup());

	it.each([
		['video', 'text-purple-500'],
		['directory', 'text-amber-500'],
		['audio', 'text-green-500'],
		['image', 'text-blue-500'],
		['something_else', 'text-gray-400']
	])('renders %s icon with %s color', (category, expectedColor) => {
		const { container } = renderComponent(FileIcon, { props: { category } });
		const svg = container.querySelector('svg');
		expect(svg).toBeInTheDocument();
		expect(svg).toHaveClass(expectedColor);
	});
});
