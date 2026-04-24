import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setTranscoderEnabled } from '$lib/stores/config';

vi.mock('@sveltejs/kit', () => ({
	redirect: (status: number, location: string) => {
		const e = new Error(`redirect ${status} ${location}`) as Error & {
			status: number;
			location: string;
		};
		e.status = status;
		e.location = location;
		throw e;
	}
}));

describe('transcoder route guard', () => {
	beforeEach(() => {
		setTranscoderEnabled(true);
	});

	it('redirects to / when transcoder is disabled', async () => {
		setTranscoderEnabled(false);
		const { load } = await import('../transcoder/+page');
		await expect(load({} as never)).rejects.toThrow(/redirect 302 \//);
	});

	it('passes through when transcoder is enabled', async () => {
		setTranscoderEnabled(true);
		const { load } = await import('../transcoder/+page');
		const result = await load({} as never);
		expect(result).toEqual({});
	});
});

describe('logs/transcoder/[filename] route guard', () => {
	beforeEach(() => {
		setTranscoderEnabled(true);
	});

	it('redirects to / when transcoder is disabled', async () => {
		setTranscoderEnabled(false);
		const { load } = await import('../logs/transcoder/[filename]/+page');
		await expect(load({} as never)).rejects.toThrow(/redirect 302 \//);
	});

	it('passes through when transcoder is enabled', async () => {
		setTranscoderEnabled(true);
		const { load } = await import('../logs/transcoder/[filename]/+page');
		const result = await load({} as never);
		expect(result).toEqual({});
	});
});
