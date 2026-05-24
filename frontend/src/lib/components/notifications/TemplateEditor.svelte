<script lang="ts">
	import { EVENT_VARIABLES, EVENT_LABELS, type EventKey, FIELD_INPUT_CLASS } from '$lib/types/notifications';
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

<div class="space-y-4">
	{#if subscribedEvents.length === 0}
		<p class="text-sm text-gray-500 dark:text-gray-400">Subscribe to an event to customize its template.</p>
	{/if}
	{#each subscribedEvents as key}
		<div class="space-y-2 rounded-md border border-primary/15 bg-page p-3 dark:border-primary/20 dark:bg-primary/5">
			<h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300">{EVENT_LABELS[key as EventKey] ?? key}</h4>
			<label class="flex flex-col gap-1">
				<span class="text-xs font-medium text-gray-600 dark:text-gray-400">Title</span>
				<input
					aria-label={`${key} title`}
					value={templates[key]?.title ?? ''}
					oninput={(e) => (ensure(key).title = (e.currentTarget as HTMLInputElement).value || null)}
					class={FIELD_INPUT_CLASS}
				/>
			</label>
			<label class="flex flex-col gap-1">
				<span class="text-xs font-medium text-gray-600 dark:text-gray-400">Body</span>
				<textarea
					aria-label={`${key} body`}
					rows="2"
					value={templates[key]?.body ?? ''}
					oninput={(e) => (ensure(key).body = (e.currentTarget as HTMLTextAreaElement).value || null)}
					class={FIELD_INPUT_CLASS}
				></textarea>
			</label>
			<p class="text-xs text-gray-500 dark:text-gray-400">
				Available variables:
				{#each varsFor(key) as v}
					<code class="mr-1 rounded bg-primary/10 px-1 py-0.5 text-primary dark:bg-primary/15">{`{${v}}`}</code>
				{/each}
			</p>
		</div>
	{/each}
</div>
