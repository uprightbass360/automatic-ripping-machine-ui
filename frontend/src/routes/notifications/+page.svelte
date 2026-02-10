<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchNotifications } from '$lib/api/notifications';
	import type { Notification } from '$lib/types/arm';
	import { formatDateTime, timeAgo } from '$lib/utils/format';

	let notifications = $state<Notification[]>([]);
	let error = $state<string | null>(null);

	onMount(async () => {
		try {
			notifications = await fetchNotifications();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load notifications';
		}
	});
</script>

<svelte:head>
	<title>Notifications - ARM UI</title>
</svelte:head>

<div class="space-y-4">
	<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Notifications</h1>

	{#if error}
		<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
			{error}
		</div>
	{:else if notifications.length === 0}
		<p class="py-8 text-center text-gray-400">No notifications.</p>
	{:else}
		<div class="space-y-3">
			{#each notifications as notification (notification.id)}
				<div
					class="rounded-lg border p-4 shadow-sm {notification.seen
						? 'border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800'
						: 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20'}"
				>
					<div class="flex items-start justify-between gap-3">
						<div>
							<h3 class="font-medium text-gray-900 dark:text-white">
								{notification.title ?? 'Notification'}
							</h3>
							{#if notification.message}
								<p class="mt-1 text-sm text-gray-600 dark:text-gray-400">{notification.message}</p>
							{/if}
						</div>
						<span class="shrink-0 text-xs text-gray-400" title={formatDateTime(notification.trigger_time)}>
							{timeAgo(notification.trigger_time)}
						</span>
					</div>
					{#if !notification.seen}
						<span class="mt-2 inline-block rounded-full bg-blue-500 px-2 py-0.5 text-xs font-medium text-white">New</span>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
