import { fetchServices } from '$lib/api/channels';
import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
	try {
		const catalog = await fetchServices();
		return { catalog };
	} catch {
		return { catalog: { featured: [], services: [] } };
	}
};
