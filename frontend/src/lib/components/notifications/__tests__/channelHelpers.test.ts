import { describe, it, expect } from 'vitest';
import { channelStatus, relativeTime, typeLabel } from '../channelHelpers';
import type { Channel } from '$lib/types/notifications';

const base: Channel = {
	id: 1, type: 'apprise', name: 'X', enabled: true,
	config: { type: 'apprise', url: 'discord://a/b' },
	subscribed_events: ['job.started'], templates: {},
	last_fired_at: null, last_success_at: null, last_error: null
};

describe('channelStatus', () => {
	it('returns off when disabled', () => {
		expect(channelStatus({ ...base, enabled: false })).toBe('off');
	});
	it('returns error when last_error set and enabled', () => {
		expect(channelStatus({ ...base, last_error: 'HTTP 500' })).toBe('error');
	});
	it('returns ok otherwise', () => {
		expect(channelStatus(base)).toBe('ok');
	});
});

describe('relativeTime', () => {
	it('returns "never" for null', () => {
		expect(relativeTime(null)).toBe('never');
	});
	it('formats minutes ago', () => {
		const tenMinAgo = new Date(Date.now() - 10 * 60 * 1000).toISOString();
		expect(relativeTime(tenMinAgo)).toMatch(/10m ago/);
	});
});

describe('typeLabel', () => {
	it('maps types to human labels', () => {
		expect(typeLabel('apprise')).toBe('Service (Apprise)');
		expect(typeLabel('webhook')).toBe('Webhook');
		expect(typeLabel('bash')).toBe('Bash script');
	});
});
