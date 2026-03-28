import { describe, it, expect, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup } from '$lib/test-utils';
import BottomStatsBar from '../BottomStatsBar.svelte';

const systemStats = {
	cpu_percent: 25,
	cpu_temp: 0,
	memory: { used_gb: 4, total_gb: 16, percent: 25 },
	storage: [
		{ name: 'Raw', path: '/home/arm/media/raw/', total_gb: 1000, used_gb: 100, free_gb: 900, percent: 10 },
		{ name: 'Completed', path: '/home/arm/media/completed/', total_gb: 1000, used_gb: 200, free_gb: 800, percent: 20 }
	],
	gpu: null
};

const transcoderStats = {
	cpu_percent: 60,
	cpu_temp: 0,
	memory: { used_gb: 8, total_gb: 32, percent: 25 },
	storage: [
		{ name: 'Work', path: '/transcode/work/', total_gb: 500, used_gb: 50, free_gb: 450, percent: 10 }
	],
	gpu: null
};

const gpuData = {
	vendor: 'nvidia',
	utilization_percent: 82,
	encoder_percent: 95,
	memory_used_mb: 4096,
	memory_total_mb: 8192,
	temperature_c: 72
};

const hwInfo = { cpu: 'Intel i7-12700', memory_total_gb: 16 };
const transcoderInfo = { cpu: 'AMD Ryzen 9', memory_total_gb: 32 };

describe('BottomStatsBar', () => {
	afterEach(() => cleanup());

	it('renders Ripper and Transcoder toggle buttons', () => {
		renderComponent(BottomStatsBar, {
			props: { systemInfo: hwInfo, systemStats }
		});
		expect(screen.getByText('Ripper')).toBeInTheDocument();
		expect(screen.getByText('Transcoder')).toBeInTheDocument();
	});

	it('shows CPU percentage when systemStats provided', () => {
		renderComponent(BottomStatsBar, {
			props: { systemInfo: hwInfo, systemStats }
		});
		expect(screen.getByText('CPU')).toBeInTheDocument();
		expect(screen.getByText('25%')).toBeInTheDocument();
	});

	it('shows memory stats when systemStats provided', () => {
		renderComponent(BottomStatsBar, {
			props: { systemInfo: hwInfo, systemStats }
		});
		expect(screen.getByText('Mem')).toBeInTheDocument();
		expect(screen.getByText('4 / 16 GB')).toBeInTheDocument();
	});

	it('shows storage volumes with links when ripper panel active', () => {
		renderComponent(BottomStatsBar, {
			props: { systemInfo: hwInfo, systemStats }
		});
		expect(screen.getByText('Raw')).toBeInTheDocument();
		expect(screen.getByText('Completed')).toBeInTheDocument();
		// Storage items should be links in ripper panel
		const rawLink = screen.getByText('Raw').closest('a');
		expect(rawLink).toBeInTheDocument();
		expect(rawLink).toHaveAttribute('href', '/files?path=%2Fhome%2Farm%2Fmedia%2Fraw');
		const completedLink = screen.getByText('Completed').closest('a');
		expect(completedLink).toBeInTheDocument();
		expect(completedLink).toHaveAttribute('href', '/files?path=%2Fhome%2Farm%2Fmedia%2Fcompleted');
	});

	it('shows free GB for storage volumes', () => {
		renderComponent(BottomStatsBar, {
			props: { systemInfo: hwInfo, systemStats }
		});
		expect(screen.getByText('900 GB')).toBeInTheDocument();
		expect(screen.getByText('800 GB')).toBeInTheDocument();
	});

	it('shows offline message when armOnline is false', () => {
		renderComponent(BottomStatsBar, {
			props: { systemInfo: hwInfo, systemStats, armOnline: false }
		});
		expect(screen.getByText('Cannot reach the ARM ripping service')).toBeInTheDocument();
	});

	it('switches to transcoder panel and shows transcoder stats', async () => {
		renderComponent(BottomStatsBar, {
			props: {
				systemInfo: hwInfo,
				systemStats,
				transcoderInfo,
				transcoderStats
			}
		});
		await fireEvent.click(screen.getByText('Transcoder'));
		expect(screen.getByText('60%')).toBeInTheDocument();
		expect(screen.getByText('8 / 32 GB')).toBeInTheDocument();
	});

	it('shows transcoder storage as plain text (not links)', async () => {
		renderComponent(BottomStatsBar, {
			props: {
				systemInfo: hwInfo,
				systemStats,
				transcoderInfo,
				transcoderStats
			}
		});
		await fireEvent.click(screen.getByText('Transcoder'));
		expect(screen.getByText('Work')).toBeInTheDocument();
		// Storage items should NOT be links in transcoder panel
		const workEl = screen.getByText('Work');
		expect(workEl.closest('a')).toBeNull();
	});

	it('shows transcoder offline message when transcoderOnline is false', async () => {
		renderComponent(BottomStatsBar, {
			props: {
				systemInfo: hwInfo,
				systemStats,
				transcoderOnline: false
			}
		});
		await fireEvent.click(screen.getByText('Transcoder'));
		expect(screen.getByText('Cannot reach the transcoder service')).toBeInTheDocument();
	});

	it('shows nothing when systemStats is null and online', () => {
		renderComponent(BottomStatsBar, {
			props: { systemInfo: null, systemStats: null }
		});
		// Toggle buttons should still render
		expect(screen.getByText('Ripper')).toBeInTheDocument();
		// But no CPU/Mem/Storage
		expect(screen.queryByText('CPU')).not.toBeInTheDocument();
		expect(screen.queryByText('Mem')).not.toBeInTheDocument();
	});

	describe('GPU tab', () => {
		it('shows GPU toggle when transcoder has GPU data', () => {
			renderComponent(BottomStatsBar, {
				props: {
					systemInfo: hwInfo,
					systemStats,
					transcoderInfo,
					transcoderStats: { ...transcoderStats, gpu: gpuData }
				}
			});
			expect(screen.getByText('GPU')).toBeInTheDocument();
		});

		it('does not show GPU toggle when gpu is null', () => {
			renderComponent(BottomStatsBar, {
				props: {
					systemInfo: hwInfo,
					systemStats,
					transcoderInfo,
					transcoderStats
				}
			});
			expect(screen.queryByRole('button', { name: 'GPU' })).not.toBeInTheDocument();
		});

		it('shows GPU metrics when GPU tab clicked', async () => {
			renderComponent(BottomStatsBar, {
				props: {
					systemInfo: hwInfo,
					systemStats,
					transcoderInfo,
					transcoderStats: { ...transcoderStats, gpu: gpuData }
				}
			});
			await fireEvent.click(screen.getByText('GPU'));
			expect(screen.getByText('nvidia')).toBeInTheDocument();
			expect(screen.getByText('Utilization')).toBeInTheDocument();
			expect(screen.getByText('82%')).toBeInTheDocument();
			expect(screen.getByText('Encoder')).toBeInTheDocument();
			expect(screen.getByText('95%')).toBeInTheDocument();
			expect(screen.getByText('VRAM')).toBeInTheDocument();
			expect(screen.getByText('4.0 / 8.0 GB')).toBeInTheDocument();
		});

		it('shows GPU temperature on GPU tab', async () => {
			renderComponent(BottomStatsBar, {
				props: {
					systemInfo: hwInfo,
					systemStats,
					transcoderInfo,
					transcoderStats: { ...transcoderStats, gpu: gpuData }
				}
			});
			await fireEvent.click(screen.getByText('GPU'));
			expect(screen.getByText(/72/)).toBeInTheDocument();
		});
	});
});
