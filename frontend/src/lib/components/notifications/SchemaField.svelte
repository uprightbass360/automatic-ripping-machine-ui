<script lang="ts">
	import type { CatalogField } from '$lib/types/notifications';

	let { field, value = $bindable() }: { field: CatalogField; value: unknown } = $props();

	const inputType = $derived(field.private ? 'password' : 'text');

	let boolValue = $derived(Boolean(value));
</script>

<label class="schema-field">
	<span class="schema-field__label">{field.label}{field.required ? ' *' : ''}</span>

	{#if field.type === 'bool'}
		<input
			type="checkbox"
			aria-label={field.label}
			checked={boolValue}
			onchange={(e) => (value = e.currentTarget.checked)}
		/>
	{:else if field.type === 'choice'}
		<select aria-label={field.label} bind:value required={field.required}>
			{#each field.values ?? [] as opt}
				<option value={opt}>{opt}</option>
			{/each}
		</select>
	{:else if field.type === 'int' || field.type === 'float'}
		<input
			type="number"
			aria-label={field.label}
			step={field.type === 'float' ? 'any' : '1'}
			bind:value
			required={field.required}
		/>
	{:else}
		<input
			type={inputType}
			aria-label={field.label}
			bind:value
			required={field.required}
		/>
	{/if}
</label>
