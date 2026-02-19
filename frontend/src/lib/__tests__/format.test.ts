import { describe, it, expect } from 'vitest';
import { formatBytes, statusColor } from '../utils/format';

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

	it('returns gray for unknown statuses', () => {
		expect(statusColor('unknown')).toBe('bg-gray-500');
		expect(statusColor(null)).toBe('bg-gray-500');
	});
});
