import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { formatBytes, statusColor, timeAgo, elapsedTime, formatDateTime } from '../utils/format';

describe('formatBytes', () => {
	it('returns "0 B" for zero bytes', () => {
		expect(formatBytes(0)).toBe('0 B');
	});

	it('formats bytes correctly', () => {
		expect(formatBytes(1024)).toBe('1 KB');
		expect(formatBytes(1048576)).toBe('1 MB');
		expect(formatBytes(1073741824)).toBe('1 GB');
	});

	it('formats fractional values', () => {
		expect(formatBytes(1536)).toBe('1.5 KB');
	});
});

describe('statusColor', () => {
	it('returns status-success for success statuses', () => {
		expect(statusColor('success')).toBe('status-success');
		expect(statusColor('completed')).toBe('status-success');
		expect(statusColor('complete')).toBe('status-success');
	});

	it('returns status-error for failure statuses', () => {
		expect(statusColor('fail')).toBe('status-error');
		expect(statusColor('failed')).toBe('status-error');
		expect(statusColor('error')).toBe('status-error');
	});

	it('returns status-warning for post-rip and waiting statuses', () => {
		expect(statusColor('copying')).toBe('status-warning');
		expect(statusColor('ejecting')).toBe('status-warning');
		expect(statusColor('waiting')).toBe('status-warning');
		expect(statusColor('waiting_transcode')).toBe('status-warning');
		expect(statusColor('pending')).toBe('status-warning');
	});

	it('returns status-active for active statuses', () => {
		expect(statusColor('identifying')).toBe('status-active');
		expect(statusColor('ready')).toBe('status-active');
		expect(statusColor('active')).toBe('status-active');
		expect(statusColor('ripping')).toBe('status-active');
	});

	it('returns status-processing for transcode statuses', () => {
		expect(statusColor('transcoding')).toBe('status-processing');
		expect(statusColor('processing')).toBe('status-processing');
	});

	it('returns status-unknown for unknown statuses and null', () => {
		expect(statusColor('unknown')).toBe('status-unknown');
		expect(statusColor(null)).toBe('status-unknown');
	});
});

describe('timeAgo', () => {
	beforeEach(() => {
		vi.useFakeTimers();
		vi.setSystemTime(new Date('2025-06-15T12:00:00Z'));
	});

	afterEach(() => {
		vi.useRealTimers();
	});

	it('returns N/A for null', () => {
		expect(timeAgo(null)).toBe('N/A');
	});

	it('returns seconds ago', () => {
		expect(timeAgo('2025-06-15T11:59:30Z')).toBe('30s ago');
	});

	it('returns minutes ago', () => {
		expect(timeAgo('2025-06-15T11:55:00Z')).toBe('5m ago');
	});

	it('returns hours ago', () => {
		expect(timeAgo('2025-06-15T09:00:00Z')).toBe('3h ago');
	});

	it('returns days ago', () => {
		expect(timeAgo('2025-06-13T12:00:00Z')).toBe('2d ago');
	});
});

describe('elapsedTime', () => {
	beforeEach(() => {
		vi.useFakeTimers();
		vi.setSystemTime(new Date('2025-06-15T12:00:00Z'));
	});

	afterEach(() => {
		vi.useRealTimers();
	});

	it('returns N/A for null', () => {
		expect(elapsedTime(null)).toBe('N/A');
	});

	it('returns seconds only for short durations', () => {
		expect(elapsedTime('2025-06-15T11:59:45Z')).toBe('15s');
	});

	it('returns minutes and seconds', () => {
		expect(elapsedTime('2025-06-15T11:57:30Z')).toBe('2m 30s');
	});

	it('returns hours and minutes', () => {
		expect(elapsedTime('2025-06-15T09:45:00Z')).toBe('2h 15m');
	});
});

describe('formatDateTime', () => {
	it('returns N/A for null', () => {
		expect(formatDateTime(null)).toBe('N/A');
	});

	it('returns a locale string for a valid date', () => {
		const result = formatDateTime('2025-06-15T12:00:00Z');
		expect(result).toBeTypeOf('string');
		expect(result).not.toBe('N/A');
		// Should contain the year
		expect(result).toContain('2025');
	});
});
