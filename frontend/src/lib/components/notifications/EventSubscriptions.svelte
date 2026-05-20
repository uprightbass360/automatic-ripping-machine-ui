<script lang="ts">
	import { EVENT_KEYS, EVENT_LABELS, type EventKey } from '$lib/types/notifications';

	let { selected = $bindable() }: { selected: string[] } = $props();

	function toggle(key: EventKey, checked: boolean) {
		if (checked) {
			if (!selected.includes(key)) selected = [...selected, key];
		} else {
			selected = selected.filter((k) => k !== key);
		}
	}
</script>

<fieldset class="event-subs">
	<legend>Events</legend>
	{#each EVENT_KEYS as key}
		<label>
			<input
				type="checkbox"
				aria-label={EVENT_LABELS[key]}
				checked={selected.includes(key)}
				onchange={(e) => toggle(key, (e.currentTarget as HTMLInputElement).checked)}
			/>
			{EVENT_LABELS[key]}
		</label>
	{/each}
</fieldset>
