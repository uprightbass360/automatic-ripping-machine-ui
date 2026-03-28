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

	describe('GPU stats', () => {
		const gpuStats = {
			...stats,
			gpu: {
				vendor: 'nvidia',
				utilization_percent: 75,
				encoder_percent: 90,
				memory_used_mb: 2048,
				memory_total_mb: 8192,
				temperature_c: 68
			}
		};

		it('renders GPU section when transcoder has GPU data', async () => {
			renderComponent(SidebarStats, {
				props: {
					systemInfo: hwInfo,
					systemStats: stats,
					transcoderInfo: { cpu: 'AMD Ryzen 9', memory_total_gb: 64 },
					transcoderStats: gpuStats
				}
			});
			await fireEvent.click(screen.getByText('Transcoder'));
			expect(screen.getByText('nvidia')).toBeInTheDocument();
			expect(screen.getByText('75%')).toBeInTheDocument();
			expect(screen.getByText('90%')).toBeInTheDocument();
			expect(screen.getByText('2.0 / 8.0 GB')).toBeInTheDocument();
		});

		it('renders GPU temperature', async () => {
			renderComponent(SidebarStats, {
				props: {
					systemInfo: hwInfo,
					systemStats: stats,
					transcoderInfo: { cpu: 'AMD Ryzen 9', memory_total_gb: 64 },
					transcoderStats: gpuStats
				}
			});
			await fireEvent.click(screen.getByText('Transcoder'));
			expect(screen.getByText(/68/)).toBeInTheDocument();
		});

		it('does not render GPU section when gpu is null', async () => {
			renderComponent(SidebarStats, {
				props: {
					systemInfo: hwInfo,
					systemStats: stats,
					transcoderInfo: { cpu: 'AMD Ryzen 9', memory_total_gb: 64 },
					transcoderStats: { ...stats, gpu: null }
				}
			});
			await fireEvent.click(screen.getByText('Transcoder'));
			expect(screen.queryByText('nvidia')).not.toBeInTheDocument();
		});

		it('renders GPU with partial fields (Intel - no VRAM/temp)', async () => {
			renderComponent(SidebarStats, {
				props: {
					systemInfo: hwInfo,
					systemStats: stats,
					transcoderInfo: { cpu: 'Intel i5', memory_total_gb: 16 },
					transcoderStats: {
						...stats,
						gpu: {
							vendor: 'intel',
							utilization_percent: 30,
							encoder_percent: 55,
							memory_used_mb: null,
							memory_total_mb: null,
							temperature_c: null
						}
					}
				}
			});
			await fireEvent.click(screen.getByText('Transcoder'));
			expect(screen.getByText('intel')).toBeInTheDocument();
			expect(screen.getByText('30%')).toBeInTheDocument();
			expect(screen.getByText('55%')).toBeInTheDocument();
			expect(screen.queryByText('VRAM')).not.toBeInTheDocument();
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
});
