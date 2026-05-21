// Hand-written types for the notification channel + catalog system.
// The BFF proxies channel data as opaque dicts, so these are not in the
// generated api.gen.ts. Catalog types mirror apprise-introspection output.

export const EVENT_KEYS = [
	'job.started',
	'job.rip_complete',
	'job.transcode_complete',
	'job.failed',
	'job.manual_wait_required',
	'job.duplicate_detected'
] as const;

export type EventKey = (typeof EVENT_KEYS)[number];

export type ChannelType = 'apprise' | 'webhook' | 'bash';

export interface AppriseConfig {
	type: 'apprise';
	url: string;
}

export interface WebhookConfig {
	type: 'webhook';
	url: string;
	shared_secret?: string | null;
	headers?: Record<string, string> | null;
}

export interface BashConfig {
	type: 'bash';
	script_path: string;
}

export type ChannelConfig = AppriseConfig | WebhookConfig | BashConfig;

export interface ChannelTemplate {
	title?: string | null;
	body?: string | null;
}

export interface Channel {
	id: number;
	type: ChannelType;
	name: string;
	enabled: boolean;
	config: ChannelConfig;
	subscribed_events: string[];
	templates: Record<string, ChannelTemplate>;
	last_fired_at: string | null;
	last_success_at: string | null;
	last_error: string | null;
}

export interface ChannelCreate {
	type: ChannelType;
	name: string;
	enabled?: boolean;
	config: ChannelConfig;
	subscribed_events: string[];
	templates?: Record<string, ChannelTemplate>;
}

export interface ChannelUpdate {
	name?: string;
	enabled?: boolean;
	config?: ChannelConfig;
	subscribed_events?: string[];
	templates?: Record<string, ChannelTemplate>;
}

export type FieldType = 'string' | 'bool' | 'choice' | 'int' | 'float';

export interface CatalogField {
	key: string;
	label: string;
	type: FieldType;
	private: boolean;
	required: boolean;
	default?: string | number | boolean | null;
	values?: string[];
}

export interface CatalogService {
	id: string;
	name: string;
	docs_url: string;
	url_scheme: string;
	required_fields: CatalogField[];
	advanced_fields: CatalogField[];
}

export interface Catalog {
	featured: string[];
	services: CatalogService[];
}

export interface DispatchRow {
	id: number;
	channel_id: number;
	event_key: string;
	status: 'pending' | 'in_flight' | 'success' | 'failed';
	attempts: number;
	last_error: string | null;
	created_at: string | null;
	completed_at: string | null;
}

export interface DispatchStatus {
	id: number;
	status: 'pending' | 'in_flight' | 'success' | 'failed';
	attempts: number;
	last_error: string | null;
	completed_at: string | null;
}

export interface TestSendResult {
	sent_at: string;
	dispatch_id: number;
}

// Per-event template variable hints, keyed off event_key. Mirrors the
// contracts event schema fields available to str.format_map on the backend.
// Per-event template variables exposed to str.format_map on the backend.
// occurred_at is available on every event (the renderer dumps the full
// event); event_id / event_key are also accepted but omitted here as
// envelope plumbing not useful in a human-facing notification.
export const EVENT_VARIABLES: Record<EventKey, string[]> = {
	'job.started': ['job_id', 'job_title', 'job_disc_type', 'job_imdb_id', 'occurred_at', 'drive_mount'],
	'job.rip_complete': ['job_id', 'job_title', 'job_disc_type', 'job_imdb_id', 'occurred_at', 'rip_duration_seconds', 'track_count'],
	'job.transcode_complete': ['job_id', 'job_title', 'job_disc_type', 'job_imdb_id', 'occurred_at', 'transcode_duration_seconds', 'output_path'],
	'job.failed': ['job_id', 'job_title', 'job_disc_type', 'job_imdb_id', 'occurred_at', 'phase', 'error_message', 'error_code'],
	'job.manual_wait_required': ['job_id', 'job_title', 'job_disc_type', 'job_imdb_id', 'occurred_at', 'wait_minutes_remaining', 'reason'],
	'job.duplicate_detected': ['job_id', 'job_title', 'job_disc_type', 'job_imdb_id', 'occurred_at', 'existing_job_id', 'existing_output_path']
};

export const EVENT_LABELS: Record<EventKey, string> = {
	'job.started': 'Job started',
	'job.rip_complete': 'Rip complete',
	'job.transcode_complete': 'Transcode complete',
	'job.failed': 'Job failed',
	'job.manual_wait_required': 'Manual wait required',
	'job.duplicate_detected': 'Duplicate detected'
};

export function isCatalogField(v: unknown): v is CatalogField {
	if (typeof v !== 'object' || v === null) return false;
	const f = v as Record<string, unknown>;
	return typeof f.key === 'string' && typeof f.label === 'string' && typeof f.type === 'string';
}
