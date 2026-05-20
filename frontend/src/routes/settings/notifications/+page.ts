import { fetchChannels } from '$lib/api/channels';
import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
	try {
		const channels = await fetchChannels();
		return { channels };
	} catch {
		return { channels: [] };
	}
};
