import { describe, it, expect, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup } from '$lib/test-utils';
import SidebarStats from './SidebarStats.svelte';

const hwInfo = { cpu: 'Intel i7-12700', memory_total_gb: 32 };
const stats = {
	cpu_percent: 45,
	cpu_temp: 55,
	memory: { used_gb: 12, total_gb: 32, percent: 37.5 },
	storage: [{ name: '/media', free_gb: 500, percent: 50 }]
};

describe('SidebarStats', () => {
	afterEach(() => cleanup());

	describe('rendering', () => {
		it('renders CPU info for ripper panel by default', () => {
			renderComponent(SidebarStats, {
				props: { systemInfo: hwInfo, systemStats: stats }
			});
			expect(screen.getByText('Intel i7-12700')).toBeInTheDocument();
		});

		it('renders CPU percentage', () => {
			renderComponent(SidebarStats, {
				props: { systemInfo: hwInfo, systemStats: stats }
			});
			expect(screen.getByText(/45%/)).toBeInTheDocument();
		});

		it('renders memory stats', () => {
			renderComponent(SidebarStats, {
				props: { systemInfo: hwInfo, systemStats: stats }
			});
			expect(screen.getByText('12 / 32 GB')).toBeInTheDocument();
		});

		it('renders storage info', () => {
			renderComponent(SidebarStats, {
				props: { systemInfo: hwInfo, systemStats: stats }
			});
			expect(screen.getByText('/media')).toBeInTheDocument();
			expect(screen.getByText('500 GB free')).toBeInTheDocument();
		});

		it('shows offline message when ARM is offline', () => {
			renderComponent(SidebarStats, {
				props: { systemInfo: hwInfo, systemStats: stats, armOnline: false }
			});
			expect(screen.getByText('Cannot reach the ARM ripping service')).toBeInTheDocument();
		});
	});

	describe('interactions', () => {
		it('switches to transcoder panel when clicked', async () => {
			renderComponent(SidebarStats, {
				props: {
					systemInfo: hwInfo,
					systemStats: stats,
					transcoderInfo: { cpu: 'AMD Ryzen 9', memory_total_gb: 64 },
					transcoderStats: { ...stats, cpu_percent: 80 }
				}
			});
			await fireEvent.click(screen.getByText('Transcoder'));
			expect(screen.getByText('AMD Ryzen 9')).toBeInTheDocument();
		});

		it('shows transcoder offline message', async () => {
			renderComponent(SidebarStats, {
				props: {
					systemInfo: hwInfo,
					systemStats: stats,
					transcoderOnline: false
				}
			});
			await fireEvent.click(screen.getByText('Transcoder'));
			expect(screen.getByText('Cannot reach the transcoder service')).toBeInTheDocument();
		});
	});

	describe('storage links', () => {
		const statsWithNamedStorage = {
			cpu_percent: 45,
			cpu_temp: 55,
			memory: { used_gb: 12, total_gb: 32, percent: 37.5 },
			storage: [
				{ name: 'Raw', path: '/home/arm/raw', free_gb: 100, total_gb: 500, used_gb: 400, percent: 80 },
				{ name: 'Completed', path: '/home/arm/completed', free_gb: 200, total_gb: 1000, used_gb: 800, percent: 80 },
			]
		};

		it('renders storage items as links for ripper panel', () => {
			const { container } = renderComponent(SidebarStats, {
				props: { systemInfo: hwInfo, systemStats: statsWithNamedStorage }
			});
			const links = container.querySelectorAll('a[href*="/files"]');
			expect(links.length).toBe(2);
			expect(links[0].getAttribute('href')).toContain('/files?path=');
			expect(links[0].getAttribute('href')).toContain('raw');
		});

		it('does not render links for transcoder panel', async () => {
			const { container } = renderComponent(SidebarStats, {
				props: {
					systemInfo: hwInfo,
					systemStats: statsWithNamedStorage,
					transcoderStats: statsWithNamedStorage,
					transcoderInfo: { cpu: 'AMD', memory_total_gb: 64 },
				}
			});
			await fireEvent.click(screen.getByText('Transcoder'));
			const links = container.querySelectorAll('a[href*="/files"]');
			expect(links.length).toBe(0);
		});
	});
});
