import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderComponent, screen, fireEvent, cleanup } from '$lib/test-utils';
import DriveCard from './DriveCard.svelte';
import type { Drive } from '$lib/types/arm';

vi.mock('$lib/api/drives', () => ({
	updateDrive: vi.fn(() => Promise.resolve()),
	scanDrive: vi.fn(() => Promise.resolve()),
	deleteDrive: vi.fn(() => Promise.resolve())
}));

function createDrive(overrides: Partial<Drive> = {}): Drive {
	return {
		drive_id: 1,
		name: 'Main Drive',
		mount: '/dev/sr0',
		job_id_current: null,
		job_id_previous: null,
		description: null,
		drive_mode: null,
		maker: 'LG',
		model: 'WH16NS40',
		serial: null,
		connection: null,
		read_cd: true,
		read_dvd: true,
		read_bd: true,
		firmware: null,
		location: null,
		stale: false,
		mdisc: null,
		serial_id: null,
		uhd_capable: false,
		current_job: null,
		...overrides
	};
}

describe('DriveCard', () => {
	afterEach(() => cleanup());

	describe('rendering', () => {
		it('renders drive name', () => {
			renderComponent(DriveCard, { props: { drive: createDrive() } });
			expect(screen.getByText('Main Drive')).toBeInTheDocument();
		});

		it('falls back to mount path when no name', () => {
			renderComponent(DriveCard, { props: { drive: createDrive({ name: null }) } });
			// mount path appears as both heading and detail
			const matches = screen.getAllByText('/dev/sr0');
			expect(matches.length).toBeGreaterThanOrEqual(1);
			// heading should use mount as name
			const heading = matches.find(el => el.tagName === 'H3');
			expect(heading).toBeDefined();
		});

		it('falls back to Drive ID when no name or mount', () => {
			renderComponent(DriveCard, { props: { drive: createDrive({ name: null, mount: null }) } });
			expect(screen.getByText('Drive 1')).toBeInTheDocument();
		});

		it('renders maker and model', () => {
			renderComponent(DriveCard, { props: { drive: createDrive() } });
			expect(screen.getByText('LG WH16NS40')).toBeInTheDocument();
		});

		it('shows Idle when no current job', () => {
			renderComponent(DriveCard, { props: { drive: createDrive() } });
			expect(screen.getByText('Idle')).toBeInTheDocument();
		});

		it('shows Stale badge for stale drives', () => {
			renderComponent(DriveCard, { props: { drive: createDrive({ stale: true }) } });
			expect(screen.getByText('Stale')).toBeInTheDocument();
		});

		it('shows disc capability badges', () => {
			renderComponent(DriveCard, { props: { drive: createDrive() } });
			expect(screen.getByText('CD')).toBeInTheDocument();
			expect(screen.getByText('DVD')).toBeInTheDocument();
			expect(screen.getByText('Blu-ray')).toBeInTheDocument();
		});

		it('shows UHD Capable checkbox for BD drives', () => {
			renderComponent(DriveCard, { props: { drive: createDrive() } });
			expect(screen.getByText('UHD Capable')).toBeInTheDocument();
		});

		it('shows Force Scan button', () => {
			renderComponent(DriveCard, { props: { drive: createDrive() } });
			expect(screen.getByText('Force Scan')).toBeInTheDocument();
		});

		it('shows Remove button for stale drives with no job', () => {
			renderComponent(DriveCard, { props: { drive: createDrive({ stale: true }) } });
			expect(screen.getByText('Remove')).toBeInTheDocument();
		});

		it('hides Remove button for non-stale drives', () => {
			renderComponent(DriveCard, { props: { drive: createDrive() } });
			expect(screen.queryByText('Remove')).not.toBeInTheDocument();
		});
	});

	describe('interactions', () => {
		it('enters edit mode when Change Name is clicked', async () => {
			renderComponent(DriveCard, { props: { drive: createDrive() } });
			await fireEvent.click(screen.getByText('Change Name'));
			expect(screen.getByDisplayValue('Main Drive')).toBeInTheDocument();
			expect(screen.getByText('Save')).toBeInTheDocument();
			expect(screen.getByText('Cancel')).toBeInTheDocument();
		});

		it('exits edit mode on Cancel', async () => {
			renderComponent(DriveCard, { props: { drive: createDrive() } });
			await fireEvent.click(screen.getByText('Change Name'));
			await fireEvent.click(screen.getByText('Cancel'));
			expect(screen.getByText('Change Name')).toBeInTheDocument();
		});
	});
});
