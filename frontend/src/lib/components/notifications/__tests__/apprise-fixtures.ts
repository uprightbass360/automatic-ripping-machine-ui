import type { Catalog, Channel } from '$lib/types/notifications';

/** Shared apprise/discord test fixtures (deduped to satisfy SonarCloud). */

export const discordCatalog: Catalog = {
	featured: ['discord'],
	services: [
		{
			id: 'discord',
			name: 'Discord',
			docs_url: '',
			url_scheme: 'discord',
			required_fields: [
				{ key: 'webhook_id', label: 'Webhook ID', type: 'string', private: false, required: true }
			],
			advanced_fields: []
		}
	]
};

export function webhookChannel(overrides: Partial<Channel> = {}): Channel {
	return {
		id: 1,
		type: 'webhook',
		name: 'Hook',
		enabled: true,
		config: { type: 'webhook', url: 'https://x' },
		subscribed_events: ['job.started'],
		templates: {},
		last_fired_at: null,
		last_success_at: null,
		last_error: null,
		...overrides
	};
}

export function appriseChannel(overrides: Partial<Channel> = {}): Channel {
	return {
		id: 1,
		type: 'apprise',
		name: 'D',
		enabled: true,
		config: { type: 'apprise', url: 'discord://1/2', service_id: 'discord' },
		subscribed_events: ['job.started'],
		templates: {},
		last_fired_at: null,
		last_success_at: null,
		last_error: null,
		...overrides
	};
}
