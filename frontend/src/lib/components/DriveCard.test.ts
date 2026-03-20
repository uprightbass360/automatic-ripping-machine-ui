import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup } from '$lib/test-utils';
import DriveCard from './DriveCard.svelte';
import type { Drive } from '$lib/types/arm';

vi.mock('$lib/api/drives', () => ({
	updateDrive: vi.fn(() => Promise.resolve()),
	scanDrive: vi.fn(() => Promise.resolve()),
	deleteDrive: vi.fn(() => Promise.resolve()),
	ejectDrive: vi.fn(() => Promise.resolve())
}));

function createDrive(overrides: Partial<Drive> = {}): Drive {
	return {
		drive_id: 1, name: 'Main Drive', mount: '/dev/sr0',
		job_id_current: null, job_id_previous: null, description: null, drive_mode: null,
		maker: 'LG', model: 'WH16NS40', serial: null, connection: null,
		read_cd: true, read_dvd: true, read_bd: true,
		firmware: null, location: null, stale: false, mdisc: null, serial_id: null,
		uhd_capable: false, current_job: null, ...overrides
	};
}

function renderDrive(overrides: Partial<Drive> = {}) {
	return renderComponent(DriveCard, { props: { drive: createDrive(overrides) } });
}

describe('DriveCard', () => {
	afterEach(() => cleanup());

	describe('rendering', () => {
		it('renders drive name, maker/model, capabilities, and action bar', () => {
			renderDrive();
			expect(screen.getByText('Main Drive')).toBeInTheDocument();
			expect(screen.getByText('Idle')).toBeInTheDocument();
			expect(screen.getByText('CD')).toBeInTheDocument();
			expect(screen.getByText('DVD')).toBeInTheDocument();
			expect(screen.getByText('Blu-ray')).toBeInTheDocument();
			// Action bar buttons
			expect(screen.getByText('Eject')).toBeInTheDocument();
			expect(screen.getByText('Insert')).toBeInTheDocument();
			expect(screen.getByText('Scan')).toBeInTheDocument();
			expect(screen.queryByText('Remove')).not.toBeInTheDocument();
		});

		it('shows drive info fields when available', () => {
			renderDrive({ connection: 'USB 3.0', firmware: '1.03' });
			expect(screen.getByText(/USB 3\.0/)).toBeInTheDocument();
			expect(screen.getByText(/FW 1\.03/)).toBeInTheDocument();
		});

		it('shows 4K tag for Blu-ray drives', () => {
			renderDrive({ read_bd: true });
			expect(screen.getByText('4K')).toBeInTheDocument();
		});

		it('hides 4K tag for non-Blu-ray drives', () => {
			renderDrive({ read_bd: false });
			expect(screen.queryByText('4K')).not.toBeInTheDocument();
		});

		it('falls back to mount path when no name', () => {
			renderDrive({ name: null });
			const matches = screen.getAllByText('/dev/sr0');
			expect(matches.find(el => el.tagName === 'H3')).toBeDefined();
		});

		it('falls back to Drive ID when no name or mount', () => {
			renderDrive({ name: null, mount: null });
			expect(screen.getByText('Drive 1')).toBeInTheDocument();
		});

		it('shows Stale badge and Remove button for stale drives', () => {
			renderDrive({ stale: true });
			expect(screen.getByText('Stale')).toBeInTheDocument();
			expect(screen.getByText('Remove')).toBeInTheDocument();
		});
	});

	describe('interactions', () => {
		it('enters and exits edit mode via Rename button', async () => {
			renderDrive();
			await fireEvent.click(screen.getByText('Rename'));
			expect(screen.getByDisplayValue('Main Drive')).toBeInTheDocument();
			expect(screen.getByText('Save')).toBeInTheDocument();
			await fireEvent.click(screen.getByText('Cancel'));
			expect(screen.getByText('Rename')).toBeInTheDocument();
		});
	});
});
