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
	it('returns green for success statuses', () => {
		expect(statusColor('success')).toBe('bg-green-500');
		expect(statusColor('completed')).toBe('bg-green-500');
		expect(statusColor('complete')).toBe('bg-green-500');
	});

	it('returns red for failure statuses', () => {
		expect(statusColor('fail')).toBe('bg-red-500');
		expect(statusColor('failed')).toBe('bg-red-500');
		expect(statusColor('error')).toBe('bg-red-500');
	});

	it('returns cyan for post-rip statuses', () => {
		expect(statusColor('copying')).toBe('bg-cyan-500');
		expect(statusColor('ejecting')).toBe('bg-cyan-500');
	});

	it('returns gray for unknown statuses', () => {
		expect(statusColor('unknown')).toBe('bg-gray-500');
		expect(statusColor(null)).toBe('bg-gray-500');
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
