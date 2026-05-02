import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { formatBytes, statusColor, statusLabel, timeAgo, elapsedTime, formatDateTime } from '../utils/format';

describe('formatBytes', () => {
	it.each([
		[0, '0 B'],
		[1024, '1 KB'],
		[1048576, '1 MB'],
		[1073741824, '1 GB'],
		[1536, '1.5 KB']
	])('formatBytes(%i) = %s', (input, expected) => {
		expect(formatBytes(input)).toBe(expected);
	});
});

describe('statusColor', () => {
	it.each<[string | null, string]>([
		// JobState (arm-neu Job.status)
		['success', 'status-success'],
		['fail', 'status-error'],
		['copying', 'status-warning'],
		['ejecting', 'status-warning'],
		['waiting', 'status-warning'],
		['waiting_transcode', 'status-warning'],
		['identifying', 'status-scanning'],
		['ready', 'status-active'],
		['ripping', 'status-active'],
		['transcoding', 'status-processing'],
		// JobStatus (transcoder TranscodeJob.status)
		['completed', 'status-success'],
		['failed', 'status-error'],
		['pending', 'status-warning'],
		['processing', 'status-processing'],
		// TrackStatus (Track.status)
		['transcoded', 'status-success'],
		// Locally-generated literals
		['importing', 'status-active'],
		['skipped', 'status-unknown'],
		// Fallthrough
		['unknown', 'status-unknown'],
		[null, 'status-unknown'],
		// Removed legacy synonyms - now fall through to status-unknown
		['active', 'status-unknown'],
		['complete', 'status-unknown'],
		['error', 'status-unknown']
	])('statusColor(%s) = %s', (input, expected) => {
		expect(statusColor(input)).toBe(expected);
	});
});

describe('statusLabel', () => {
	it.each<[string | null, string]>([
		['identifying', 'Scanning'],
		['ripping', 'Ripping'],
		['success', 'Success'],
		['fail', 'Failed'],
		['waiting', 'Waiting'],
		['transcoding', 'Transcoding'],
		['info', 'Scanning'],
		[null, 'Unknown'],
	])('statusLabel(%s) = %s', (input, expected) => {
		expect(statusLabel(input)).toBe(expected);
	});
});

describe('timeAgo', () => {
	beforeEach(() => {
		vi.useFakeTimers();
		vi.setSystemTime(new Date('2025-06-15T12:00:00Z'));
	});
	afterEach(() => vi.useRealTimers());

	it.each([
		[null, 'N/A'],
		['2025-06-15T11:59:30Z', '30s ago'],
		['2025-06-15T11:55:00Z', '5m ago'],
		['2025-06-15T09:00:00Z', '3h ago'],
		['2025-06-13T12:00:00Z', '2d ago']
	])('timeAgo(%s) = %s', (input, expected) => {
		expect(timeAgo(input)).toBe(expected);
	});
});

describe('elapsedTime', () => {
	beforeEach(() => {
		vi.useFakeTimers();
		vi.setSystemTime(new Date('2025-06-15T12:00:00Z'));
	});
	afterEach(() => vi.useRealTimers());

	it.each([
		[null, 'N/A'],
		['2025-06-15T11:59:45Z', '15s'],
		['2025-06-15T11:57:30Z', '2m 30s'],
		['2025-06-15T09:45:00Z', '2h 15m']
	])('elapsedTime(%s) = %s', (input, expected) => {
		expect(elapsedTime(input)).toBe(expected);
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
		expect(result).toContain('2025');
	});
});
