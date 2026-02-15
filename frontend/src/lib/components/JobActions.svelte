<script lang="ts">
	import type { Job } from '$lib/types/arm';
	import { abandonJob, deleteJob, fixJobPermissions } from '$lib/api/jobs';
	import { isJobActive } from '$lib/utils/job-type';

	interface Props {
		job: Job;
		onaction?: () => void;
		compact?: boolean;
	}

	let { job, onaction, compact = false }: Props = $props();

	let loading = $state<string | null>(null);
	let feedback = $state<{ type: 'success' | 'error'; message: string } | null>(null);

	let active = $derived(isJobActive(job.status));
	let statusLower = $derived(job.status?.toLowerCase() ?? '');
	let canAbandon = $derived(active);
	let canDelete = $derived(statusLower === 'success' || statusLower === 'fail');
	let canFixPerms = $derived(statusLower === 'success');

	function clearFeedback() {
		setTimeout(() => (feedback = null), 3000);
	}

	async function handleAbandon() {
		if (!confirm(`Abandon job "${job.title || job.label || job.job_id}"?`)) return;
		loading = 'abandon';
		feedback = null;
		try {
			await abandonJob(job.job_id);
			feedback = { type: 'success', message: 'Job abandoned' };
			onaction?.();
		} catch (e) {
			feedback = { type: 'error', message: e instanceof Error ? e.message : 'Failed to abandon' };
		} finally {
			loading = null;
			clearFeedback();
		}
	}

	async function handleDelete() {
		if (!confirm(`Delete job "${job.title || job.label || job.job_id}"? This cannot be undone.`)) return;
		loading = 'delete';
		feedback = null;
		try {
			await deleteJob(job.job_id);
			feedback = { type: 'success', message: 'Job deleted' };
			onaction?.();
		} catch (e) {
			feedback = { type: 'error', message: e instanceof Error ? e.message : 'Failed to delete' };
		} finally {
			loading = null;
			clearFeedback();
		}
	}

	async function handleFixPerms() {
		if (!confirm(`Fix permissions for job "${job.title || job.label || job.job_id}"?`)) return;
		loading = 'fixperms';
		feedback = null;
		try {
			await fixJobPermissions(job.job_id);
			feedback = { type: 'success', message: 'Permissions fixed' };
			onaction?.();
		} catch (e) {
			feedback = { type: 'error', message: e instanceof Error ? e.message : 'Failed to fix permissions' };
		} finally {
			loading = null;
			clearFeedback();
		}
	}

	let btnBase = $derived(
		compact
			? 'rounded px-2 py-0.5 text-xs font-medium disabled:opacity-50'
			: 'rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-50'
	);
</script>

{#if canAbandon || canDelete || canFixPerms}
	<div class="flex items-center gap-1.5 flex-wrap">
		{#if canAbandon}
			<button
				onclick={handleAbandon}
				disabled={loading !== null}
				class="{btnBase} bg-yellow-100 text-yellow-700 hover:bg-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-400 dark:hover:bg-yellow-900/50"
			>
				{loading === 'abandon' ? 'Abandoning...' : 'Abandon'}
			</button>
		{/if}
		{#if canFixPerms}
			<button
				onclick={handleFixPerms}
				disabled={loading !== null}
				class="{btnBase} bg-primary-light-bg text-primary-text hover:bg-primary/20 dark:bg-primary-light-bg-dark/30 dark:text-primary-text-dark dark:hover:bg-primary/20"
			>
				{loading === 'fixperms' ? 'Fixing...' : 'Fix Perms'}
			</button>
		{/if}
		{#if canDelete}
			<button
				onclick={handleDelete}
				disabled={loading !== null}
				class="{btnBase} bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50"
			>
				{loading === 'delete' ? 'Deleting...' : 'Delete'}
			</button>
		{/if}
		{#if feedback}
			<span class="text-xs {feedback.type === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
				{feedback.message}
			</span>
		{/if}
	</div>
{/if}
