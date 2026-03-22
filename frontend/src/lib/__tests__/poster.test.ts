import { describe, it, expect } from 'vitest';
import { posterSrc } from '../utils/poster';

describe('posterSrc', () => {
	it('returns empty string for null', () => {
		expect(posterSrc(null)).toBe('');
	});

	it('returns empty string for undefined', () => {
		expect(posterSrc(undefined)).toBe('');
	});

	it('returns empty string for empty string', () => {
		expect(posterSrc('')).toBe('');
	});

	it('returns relative path unchanged', () => {
		expect(posterSrc('/images/poster.jpg')).toBe('/images/poster.jpg');
	});

	it('proxies http URL through backend', () => {
		const url = 'http://m.media-amazon.com/images/poster.jpg';
		expect(posterSrc(url)).toBe(
			`/api/jobs/folder/poster-proxy?url=${encodeURIComponent(url)}`
		);
	});

	it('proxies https URL through backend', () => {
		const url = 'https://image.tmdb.org/t/p/w500/poster.jpg';
		expect(posterSrc(url)).toBe(
			`/api/jobs/folder/poster-proxy?url=${encodeURIComponent(url)}`
		);
	});

	it('returns path-only strings unchanged', () => {
		expect(posterSrc('poster.jpg')).toBe('poster.jpg');
	});
});
