<script lang="ts">
	import { EVENT_VARIABLES, EVENT_LABELS, type EventKey } from '$lib/types/notifications';
	import type { ChannelTemplate } from '$lib/types/notifications';

	let {
		subscribedEvents,
		templates = $bindable()
	}: { subscribedEvents: string[]; templates: Record<string, ChannelTemplate> } = $props();

	function ensure(key: string): ChannelTemplate {
		if (!templates[key]) templates[key] = { title: null, body: null };
		return templates[key];
	}

	function varsFor(key: string): string[] {
		return EVENT_VARIABLES[key as EventKey] ?? [];
	}
</script>

<div class="template-editor">
	{#each subscribedEvents as key}
		<div class="template-editor__event">
			<h4>{EVENT_LABELS[key as EventKey] ?? key}</h4>
			<label>
				Title
				<input
					aria-label={`${key} title`}
					value={templates[key]?.title ?? ''}
					oninput={(e) => (ensure(key).title = (e.currentTarget as HTMLInputElement).value || null)}
				/>
			</label>
			<label>
				Body
				<textarea
					aria-label={`${key} body`}
					value={templates[key]?.body ?? ''}
					oninput={(e) => (ensure(key).body = (e.currentTarget as HTMLTextAreaElement).value || null)}
				></textarea>
			</label>
			<p class="template-editor__vars">
				Available variables:
				{#each varsFor(key) as v}
					<code>{`{${v}}`}</code>
				{/each}
			</p>
		</div>
	{/each}
</div>
