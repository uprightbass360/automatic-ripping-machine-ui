import { describe, it, expect } from 'vitest';
import { getVideoTypeConfig, discTypeLabel, isJobActive } from '../utils/job-type';

describe('getVideoTypeConfig', () => {
	it('returns fallback for null', () => {
		const config = getVideoTypeConfig(null);
		expect(config.label).toBe('Disc');
		expect(config.icon).toBe('disc');
	});

	it('returns correct config for known types', () => {
		expect(getVideoTypeConfig('movie').label).toBe('Movie');
		expect(getVideoTypeConfig('series').label).toBe('Series');
		expect(getVideoTypeConfig('music').label).toBe('Music');
		expect(getVideoTypeConfig('data').label).toBe('Data');
	});

	it('is case-insensitive', () => {
		expect(getVideoTypeConfig('Movie').label).toBe('Movie');
		expect(getVideoTypeConfig('SERIES').label).toBe('Series');
	});

	it('returns fallback for unknown type', () => {
		expect(getVideoTypeConfig('audiobook').label).toBe('Disc');
	});
});

describe('discTypeLabel', () => {
	it('returns Unknown for null and undefined', () => {
		expect(discTypeLabel(null)).toBe('Unknown');
		expect(discTypeLabel(undefined)).toBe('Unknown');
	});

	it('returns proper labels for known disc types', () => {
		expect(discTypeLabel('dvd')).toBe('DVD');
		expect(discTypeLabel('bluray')).toBe('Blu-ray');
		expect(discTypeLabel('bluray4k')).toBe('4K UHD');
		expect(discTypeLabel('music')).toBe('Music CD');
		expect(discTypeLabel('data')).toBe('Data');
	});

	it('is case-insensitive', () => {
		expect(discTypeLabel('DVD')).toBe('DVD');
		expect(discTypeLabel('BluRay')).toBe('Blu-ray');
	});

	it('returns input as-is for unknown types', () => {
		expect(discTypeLabel('laserdisc')).toBe('laserdisc');
	});
});

describe('isJobActive', () => {
	it('returns false for null', () => {
		expect(isJobActive(null)).toBe(false);
	});

	it('returns true for active statuses', () => {
		expect(isJobActive('identifying')).toBe(true);
		expect(isJobActive('ready')).toBe(true);
		expect(isJobActive('active')).toBe(true);
		expect(isJobActive('ripping')).toBe(true);
		expect(isJobActive('processing')).toBe(true);
		expect(isJobActive('transcoding')).toBe(true);
		expect(isJobActive('pending')).toBe(true);
		expect(isJobActive('waiting')).toBe(true);
		expect(isJobActive('waiting_transcode')).toBe(true);
	});

	it('is case-insensitive', () => {
		expect(isJobActive('Identifying')).toBe(true);
		expect(isJobActive('RIPPING')).toBe(true);
	});

	it('returns false for terminal statuses', () => {
		expect(isJobActive('success')).toBe(false);
		expect(isJobActive('fail')).toBe(false);
		expect(isJobActive('completed')).toBe(false);
		expect(isJobActive('error')).toBe(false);
	});
});
