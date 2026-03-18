import { describe, it, expect, afterEach } from 'vitest';
import { renderComponent, screen, cleanup } from '$lib/test-utils';
import DiscTypeIcon from './DiscTypeIcon.svelte';

describe('DiscTypeIcon', () => {
	afterEach(() => cleanup());

	describe('rendering', () => {
		it('renders DVD icon for dvd disctype', () => {
			renderComponent(DiscTypeIcon, { props: { disctype: 'dvd' } });
			const img = screen.getByAltText('DVD');
			expect(img).toBeInTheDocument();
			expect(img).toHaveAttribute('src', '/img/disc-dvd.svg');
		});

		it('renders Blu-ray icon for bluray disctype', () => {
			renderComponent(DiscTypeIcon, { props: { disctype: 'bluray' } });
			const img = screen.getByAltText('Blu-ray');
			expect(img).toHaveAttribute('src', '/img/disc-bluray.svg');
		});

		it('renders 4K UHD icon for bluray4k disctype', () => {
			renderComponent(DiscTypeIcon, { props: { disctype: 'bluray4k' } });
			const img = screen.getByAltText('4K UHD');
			expect(img).toHaveAttribute('src', '/img/disc-bluray4k.svg');
		});

		it('renders CD icon for music disctype', () => {
			renderComponent(DiscTypeIcon, { props: { disctype: 'music' } });
			const img = screen.getByAltText('CD');
			expect(img).toHaveAttribute('src', '/img/disc-music.svg');
		});

		it('renders unknown icon for null disctype', () => {
			renderComponent(DiscTypeIcon, { props: { disctype: null } });
			const img = screen.getByAltText('Unknown');
			expect(img).toHaveAttribute('src', '/img/disc-unknown.svg');
		});

		it('renders unknown icon for unrecognized disctype', () => {
			renderComponent(DiscTypeIcon, { props: { disctype: 'laserdisc' } });
			const img = screen.getByAltText('Unknown');
			expect(img).toHaveAttribute('src', '/img/disc-unknown.svg');
		});
	});

	describe('props', () => {
		it('applies default size class', () => {
			renderComponent(DiscTypeIcon, { props: { disctype: 'dvd' } });
			const img = screen.getByAltText('DVD');
			expect(img).toHaveClass('h-6', 'w-6');
		});

		it('applies custom size class', () => {
			renderComponent(DiscTypeIcon, { props: { disctype: 'dvd', size: 'h-4 w-4' } });
			const img = screen.getByAltText('DVD');
			expect(img).toHaveClass('h-4', 'w-4');
		});
	});
});
