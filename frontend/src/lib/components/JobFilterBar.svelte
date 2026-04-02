<script lang="ts">
	interface Props {
		statusFilter: string;
		videoTypeFilter: string;
		disctypeFilter: string;
		daysFilter: number | undefined;
		onstatusfilter: (value: string) => void;
		onvideotypefilter: (value: string) => void;
		ondisctypefilter: (value: string) => void;
		ondaysfilter: (value: number | undefined) => void;
		onsearch: (e: Event) => void;
	}

	let {
		statusFilter,
		videoTypeFilter,
		disctypeFilter,
		daysFilter,
		onstatusfilter,
		onvideotypefilter,
		ondisctypefilter,
		ondaysfilter,
		onsearch
	}: Props = $props();

	const pillBase = 'px-2.5 py-1 rounded-md text-xs font-semibold cursor-pointer transition-colors';
	const pillActive =
		'bg-primary/20 text-primary-text dark:bg-primary/25 dark:text-primary-text-dark outline outline-2 outline-primary/40';
	const pillInactive =
		'bg-primary/5 text-gray-500 hover:bg-primary/10 dark:bg-primary/10 dark:text-gray-400 hover:dark:bg-primary/15';

	const statusPills = [
		{ label: 'All', value: '' },
		{ label: 'Active', value: 'active' },
		{ label: 'Success', value: 'success' },
		{ label: 'Failed', value: 'fail' },
		{ label: 'Waiting', value: 'waiting' }
	];

	const typePills = [
		{ label: 'All', value: '' },
		{ label: 'Movie', value: 'movie' },
		{ label: 'Series', value: 'series' },
		{ label: 'Music', value: 'music' }
	];

	const discTypes = [
		{ label: 'All', value: '' },
		{ label: 'Blu-ray', value: 'bluray' },
		{ label: 'DVD', value: 'dvd' },
		{ label: 'CD', value: 'music' },
		{ label: 'Data', value: 'data' }
	];

	const daysOptions = [
		{ label: 'All Time', value: undefined as number | undefined },
		{ label: '7 days', value: 7 },
		{ label: '30 days', value: 30 },
		{ label: '90 days', value: 90 }
	];
</script>

<!-- Row 1: Search | Status pills | Type pills -->
<div class="flex flex-wrap items-center gap-3">
	<input
		type="text"
		placeholder="Search titles..."
		oninput={onsearch}
		class="lcars-input w-48 rounded-lg border border-primary/25 bg-primary/5 px-3 py-2 text-sm dark:border-primary/30 dark:bg-primary/10 dark:text-white"
	/>

	<div class="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>

	<!-- Status pills -->
	<div class="flex flex-wrap gap-1.5">
		{#each statusPills as pill}
			<button
				onclick={() => onstatusfilter(pill.value)}
				class="{pillBase} {statusFilter === pill.value ? pillActive : pillInactive}"
			>{pill.label}</button>
		{/each}
	</div>

	<div class="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>

	<!-- Type pills -->
	<div class="flex flex-wrap gap-1.5">
		{#each typePills as pill}
			<button
				onclick={() => onvideotypefilter(pill.value)}
				class="{pillBase} {videoTypeFilter === pill.value ? pillActive : pillInactive}"
			>{pill.label}</button>
		{/each}
	</div>
</div>

<!-- Row 2: Disc pills | Time range -->
<div class="flex flex-wrap items-center gap-3">
	<!-- Disc pills -->
	<div class="flex flex-wrap gap-1.5">
		{#each discTypes as disc}
			<button
				onclick={() => ondisctypefilter(disc.value)}
				class="{pillBase} {disctypeFilter === disc.value ? pillActive : pillInactive}"
			>{disc.label}</button>
		{/each}
	</div>

	<div class="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>

	<!-- Time range select -->
	<select
		value={daysFilter ?? ''}
		onchange={(e) => {
			const val = (e.target as HTMLSelectElement).value;
			ondaysfilter(val ? Number(val) : undefined);
		}}
		class="lcars-input rounded-lg border border-primary/25 bg-primary/5 px-3 py-1.5 text-xs dark:border-primary/30 dark:bg-primary/10 dark:text-white"
	>
		{#each daysOptions as opt}
			<option value={opt.value ?? ''}>{opt.label}</option>
		{/each}
	</select>
</div>
