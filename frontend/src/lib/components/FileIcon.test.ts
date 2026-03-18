import { describe, it, expect, afterEach } from 'vitest';
import { renderComponent, cleanup } from '$lib/test-utils';
import FileIcon from './FileIcon.svelte';

describe('FileIcon', () => {
	afterEach(() => cleanup());

	describe('rendering', () => {
		it('renders an SVG for a known category', () => {
			const { container } = renderComponent(FileIcon, { props: { category: 'video' } });
			const svg = container.querySelector('svg');
			expect(svg).toBeInTheDocument();
			expect(svg).toHaveClass('text-purple-500');
		});

		it('renders directory icon with amber color', () => {
			const { container } = renderComponent(FileIcon, { props: { category: 'directory' } });
			const svg = container.querySelector('svg');
			expect(svg).toHaveClass('text-amber-500');
		});

		it('renders audio icon with green color', () => {
			const { container } = renderComponent(FileIcon, { props: { category: 'audio' } });
			const svg = container.querySelector('svg');
			expect(svg).toHaveClass('text-green-500');
		});

		it('falls back to other icon for unknown category', () => {
			const { container } = renderComponent(FileIcon, { props: { category: 'something_else' } });
			const svg = container.querySelector('svg');
			expect(svg).toHaveClass('text-gray-400');
		});
	});
});
