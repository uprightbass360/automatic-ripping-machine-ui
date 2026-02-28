<script lang="ts">
	import type { LogEntry, StructuredLogContent } from '$lib/types/arm';
	import { fetchStructuredLogContent } from '$lib/api/logs';

	interface Props {
		logfile: string;
		maxEntries?: number;
		levelFilter?: string;
		autoRefresh?: boolean;
		containerClass?: string;
		fetchFn?: (
			filename: string,
			mode: 'tail' | 'full',
			lines: number,
			level?: string,
			search?: string
		) => Promise<StructuredLogContent>;
		logLinkBase?: string;
	}

	let {
		logfile,
		maxEntries = 10,
		levelFilter,
		autoRefresh = true,
		containerClass,
		fetchFn = fetchStructuredLogContent,
		logLinkBase = '/logs',
	}: Props = $props();

	let entries = $state<LogEntry[]>([]);
	let error = $state<string | null>(null);
	let loading = $state(true);
	let expanded = $state(false);

	let errorCount = $derived(entries.filter((e) => e.level === 'error' || e.level === 'critical').length);
	let warningCount = $derived(entries.filter((e) => e.level === 'warning').length);

	const levelBadgeColors: Record<string, string> = {
		error: 'bg-red-900/60 text-red-300',
		critical: 'bg-red-900/60 text-red-300',
		warning: 'bg-yellow-900/60 text-yellow-300',
		info: 'bg-emerald-900/40 text-emerald-400',
		debug: 'bg-gray-700/60 text-gray-400',
	};

	const borderColors: Record<string, string> = {
		error: 'border-l-red-500',
		critical: 'border-l-red-500',
		warning: 'border-l-yellow-500',
		info: 'border-l-transparent',
		debug: 'border-l-transparent',
	};

	async function load() {
		try {
			const data = await fetchFn(
				logfile,
				'tail',
				maxEntries,
				levelFilter || undefined
			);
			entries = data.entries.toReversed();
			error = null;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load log';
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		logfile; maxEntries; levelFilter;
		loading = true;
		load();
	});

	let timer: ReturnType<typeof setInterval> | null = null;
	$effect(() => {
		if (autoRefresh) {
			timer = setInterval(load, 5000);
		}
		return () => {
			if (timer) clearInterval(timer);
		};
	});
</script>

{#if error}
	<div class={containerClass ?? ''}>
		<div class="text-sm text-red-400">{error}</div>
	</div>
{:else if entries.length > 0}
	<div class={containerClass ?? ''}>
		<div class="rounded-lg border border-gray-200 dark:border-gray-700">
			<!-- Summary header -->
			<button
				onclick={() => (expanded = !expanded)}
				class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50"
			>
				<svg
					class="h-4 w-4 text-gray-400 transition-transform {expanded ? 'rotate-90' : ''}"
					fill="none" stroke="currentColor" viewBox="0 0 24 24"
				>
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
				</svg>
				<span class="font-medium text-gray-700 dark:text-gray-300">Recent Log</span>
				{#if errorCount > 0}
					<span class="rounded-sm bg-red-100 px-1.5 py-0.5 text-xs font-medium text-red-700 dark:bg-red-900/30 dark:text-red-400">
						{errorCount} error{errorCount !== 1 ? 's' : ''}
					</span>
				{/if}
				{#if warningCount > 0}
					<span class="rounded-sm bg-yellow-100 px-1.5 py-0.5 text-xs font-medium text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400">
						{warningCount} warning{warningCount !== 1 ? 's' : ''}
					</span>
				{/if}
				<span class="ml-auto text-xs text-gray-400">{entries.length} entries</span>
			</button>

			{#if expanded}
				<div class="border-t border-gray-200 dark:border-gray-700">
					<div class="max-h-64 overflow-auto">
						{#each entries as entry}
							<div class="flex items-start gap-2 border-b border-l-2 border-b-gray-100 px-3 py-1.5 font-mono text-xs dark:border-b-gray-800 {borderColors[entry.level] ?? 'border-l-transparent'}">
								<span class="inline-block w-12 shrink-0 rounded px-1 py-0.5 text-center text-[10px] font-semibold uppercase {levelBadgeColors[entry.level] ?? 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'}">
									{entry.level}
								</span>
								{#if entry.timestamp}
									<span class="shrink-0 text-gray-400">{entry.timestamp.replace('T', ' ').replace('Z', '').slice(11, 19)}</span>
								{/if}
								<span class="min-w-0 break-words text-gray-700 dark:text-gray-300">{entry.event}</span>
							</div>
						{/each}
					</div>
					<div class="border-t border-gray-200 px-3 py-2 dark:border-gray-700">
						<a
							href="{logLinkBase}/{logfile}"
							class="text-xs text-primary-text hover:underline dark:text-primary-text-dark"
						>
							View full log &rarr;
						</a>
					</div>
				</div>
			{/if}
		</div>
	</div>
{/if}
