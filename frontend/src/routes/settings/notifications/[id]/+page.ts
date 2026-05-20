import { fetchChannel, fetchDispatches } from '$lib/api/channels';
import type { DispatchRow } from '$lib/types/notifications';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params }) => {
	const id = Number(params.id);
	const channel = await fetchChannel(id);
	let dispatches: DispatchRow[] = [];
	try {
		dispatches = await fetchDispatches({ channelId: id, limit: 20 });
	} catch {
		dispatches = [];
	}
	return { channel, dispatches };
};
