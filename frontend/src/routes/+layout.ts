import { redirect } from '@sveltejs/kit';
import type { LayoutLoad } from './$types';

export const prerender = false;
export const ssr = false;

export const load: LayoutLoad = async ({ url, fetch }) => {
	// Skip setup check if already on /setup
	if (url.pathname.startsWith('/setup')) return {};

	try {
		const resp = await fetch('/api/setup/status');
		if (resp.ok) {
			const status = await resp.json();
			if (status.first_run === true) {
				redirect(307, '/setup');
			}
		}
	} catch (e) {
		// Re-throw SvelteKit redirects (they use throw internally)
		if (e && typeof e === 'object' && 'status' in e && 'location' in e) throw e;
		// ARM unreachable — don't redirect, let the normal UI handle it
	}

	return {};
};
