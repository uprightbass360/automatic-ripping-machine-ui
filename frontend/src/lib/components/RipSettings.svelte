<script lang="ts">
	import type { Job, JobConfigUpdate } from '$lib/types/arm';
	import { updateJobConfig } from '$lib/api/jobs';

	interface Props {
		job: Job;
		config: Record<string, string | null>;
		isMusic?: boolean;
		onsaved?: () => void;
	}

	let { job, config, isMusic = false, onsaved }: Props = $props();

	let ripmethod = $state(String(config.RIPMETHOD ?? 'mkv').toLowerCase());
	let disctype = $state(String(config.DISCTYPE ?? job.disctype ?? 'dvd').toLowerCase());
	let mainfeature = $state(
		config.MAINFEATURE === '1' || String(config.MAINFEATURE ?? '').toLowerCase() === 'true'
	);
	let minlength = $state(Number(config.MINLENGTH) || 120);
	let maxlength = $state(Number(config.MAXLENGTH) || 99999);

	let saving = $state(false);
	let feedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);

	async function handleSave() {
		saving = true;
		feedback = null;
		try {
			const data: Partial<JobConfigUpdate> = {
				RIPMETHOD: ripmethod as 'mkv' | 'backup',
				DISCTYPE: disctype as 'dvd' | 'bluray' | 'bluray4k' | 'music' | 'data',
				MAINFEATURE: mainfeature,
				MINLENGTH: minlength,
				MAXLENGTH: maxlength
			};
			await updateJobConfig(job.job_id, data);
			feedback = { type: 'success', message: 'Settings saved' };
			onsaved?.();
		} catch (e) {
			feedback = { type: 'error', message: e instanceof Error ? e.message : 'Save failed' };
		} finally {
			saving = false;
		}
	}

	const inputClass =
		'rounded-lg border border-primary/25 bg-primary/5 px-3 py-1.5 text-sm text-gray-900 focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary dark:border-primary/30 dark:bg-primary/10 dark:text-white';
	const labelClass = 'text-sm font-medium text-gray-700 dark:text-gray-300';
	const btnBase =
		'rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-50 transition-colors';
</script>

<div class="space-y-4">
	<div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
		{#if !isMusic}
			<label class="space-y-1">
				<span class={labelClass}>Rip Method</span>
				<select bind:value={ripmethod} class="{inputClass} w-full">
					<option value="mkv">MKV</option>
					<option value="backup">Backup (ISO)</option>
				</select>
			</label>
		{/if}

		<label class="space-y-1">
			<span class={labelClass}>Disc Type</span>
			<select bind:value={disctype} class="{inputClass} w-full">
				<option value="dvd">DVD</option>
				<option value="bluray">Blu-ray</option>
				<option value="bluray4k">4K UHD</option>
				<option value="music">Music</option>
				<option value="data">Data</option>
			</select>
		</label>

		{#if !isMusic}
			<div class="space-y-1">
				<label class="flex items-center gap-2">
					<input
						type="checkbox"
						bind:checked={mainfeature}
						class="h-4 w-4 rounded-sm border-primary/25 text-primary focus:ring-primary dark:border-primary/30 dark:bg-primary/10"
					/>
					<span class={labelClass}>Main Feature Only</span>
				</label>
				<p class="text-xs text-gray-500 dark:text-gray-400">Rip only the longest title, skipping extras and bonus features</p>
			</div>

			<label class="space-y-1">
				<span class={labelClass}>Min Length (s)</span>
				<input type="number" bind:value={minlength} min="0" class="{inputClass} w-full" />
			</label>

			<label class="space-y-1">
				<span class={labelClass}>Max Length (s)</span>
				<input type="number" bind:value={maxlength} min="0" class="{inputClass} w-full" />
			</label>
		{/if}
	</div>

	<div class="flex items-center gap-2">
		<button
			onclick={handleSave}
			disabled={saving}
			class="{btnBase} bg-green-600 text-white hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600"
		>
			{saving ? 'Saving...' : 'Save Settings'}
		</button>
		{#if feedback}
			<span
				class="text-xs {feedback.type === 'success'
					? 'text-green-600 dark:text-green-400'
					: 'text-red-600 dark:text-red-400'}"
			>
				{feedback.message}
			</span>
		{/if}
	</div>
</div>
