import type { Channel, ChannelType } from '$lib/types/notifications';

export type ChannelStatus = 'ok' | 'warn' | 'error' | 'off';

export function channelStatus(c: Channel): ChannelStatus {
	if (!c.enabled) return 'off';
	if (c.last_error) return 'error';
	return 'ok';
}

export function relativeTime(iso: string | null): string {
	if (!iso) return 'never';
	const then = new Date(iso).getTime();
	const diffMs = Date.now() - then;
	const min = Math.floor(diffMs / 60000);
	if (min < 1) return 'just now';
	if (min < 60) return `${min}m ago`;
	const hr = Math.floor(min / 60);
	if (hr < 24) return `${hr}h ago`;
	const day = Math.floor(hr / 24);
	return `${day}d ago`;
}

const TYPE_LABELS: Record<ChannelType, string> = {
	apprise: 'Service (Apprise)',
	webhook: 'Webhook',
	bash: 'Bash script'
};

export function typeLabel(type: ChannelType): string {
	return TYPE_LABELS[type] ?? type;
}
