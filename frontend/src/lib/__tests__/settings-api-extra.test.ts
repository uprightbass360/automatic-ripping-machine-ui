import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

function jsonResponse(data: unknown, ok = true) {
	return { ok, status: ok ? 200 : 500, statusText: ok ? 'OK' : 'Error', json: () => Promise.resolve(data) };
}

import { fetchAbcdeConfig, saveAbcdeConfig, testTranscoderConnection, testTranscoderWebhook, fetchSystemInfo } from '../api/settings';

beforeEach(() => mockFetch.mockReset());

describe('fetchAbcdeConfig', () => {
	it('GETs /api/settings/abcde', async () => {
		mockFetch.mockResolvedValue(jsonResponse({ content: 'CDROM=/dev/sr0', path: '/etc/abcde.conf', exists: true }));
		const result = await fetchAbcdeConfig();
		expect(result.content).toBe('CDROM=/dev/sr0');
		expect(result.exists).toBe(true);
	});
});

describe('saveAbcdeConfig', () => {
	it('PUTs content to /api/settings/abcde', async () => {
		mockFetch.mockResolvedValue(jsonResponse({ success: true }));
		await saveAbcdeConfig('CDROM=/dev/sr1');
		expect(mockFetch).toHaveBeenCalledWith('/api/settings/abcde', expect.objectContaining({
			method: 'PUT',
			body: JSON.stringify({ content: 'CDROM=/dev/sr1' })
		}));
	});
});

describe('testTranscoderConnection', () => {
	it('POSTs to /api/settings/transcoder/test-connection', async () => {
		mockFetch.mockResolvedValue(jsonResponse({ reachable: true, auth_ok: true, auth_required: false, gpu_support: null, worker_running: true, queue_size: 0, error: null }));
		const result = await testTranscoderConnection();
		expect(result.reachable).toBe(true);
	});
});

describe('testTranscoderWebhook', () => {
	it('POSTs secret to /api/settings/transcoder/test-webhook', async () => {
		mockFetch.mockResolvedValue(jsonResponse({ reachable: true, secret_ok: true, secret_required: true, error: null }));
		const result = await testTranscoderWebhook('my-secret');
		expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/test-webhook'), expect.objectContaining({
			method: 'POST',
			body: JSON.stringify({ webhook_secret: 'my-secret' })
		}));
		expect(result.secret_ok).toBe(true);
	});
});

describe('fetchSystemInfo', () => {
	it('GETs /api/settings/system-info', async () => {
		mockFetch.mockResolvedValue(jsonResponse({ versions: {}, endpoints: {}, paths: [], database: {}, drives: [] }));
		const result = await fetchSystemInfo();
		expect(result.versions).toBeDefined();
	});
});
