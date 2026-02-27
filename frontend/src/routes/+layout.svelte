<script lang="ts">
	import '../app.css';
	import { page } from '$app/stores';
	import { theme, toggleTheme } from '$lib/stores/theme';
	import { colorScheme } from '$lib/stores/colorScheme';
	import { dashboard } from '$lib/stores/dashboard';
	import SidebarStats from '$lib/components/SidebarStats.svelte';
	import { onMount } from 'svelte';
	let { children } = $props();

	let sidebarOpen = $state(false);

	onMount(() => {
		// Apply initial theme class
		document.documentElement.classList.toggle('dark', $theme === 'dark');

		// Start dashboard polling (provides sidebar stats on all pages)
		dashboard.start();
		return () => dashboard.stop();
	});

	const navItems = [
		{ href: '/', label: 'Dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
		{ href: '/drives', label: 'Drives', icon: 'M4 6h16v12H4V6zM4 11h16M18 15h.01' },
		{ href: '/logs', label: 'Logs', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
		{ href: '/settings', label: 'Settings', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z' },
	];

	function isActive(href: string, pathname: string): boolean {
		if (href === '/') return pathname === '/';
		return pathname.startsWith(href);
	}
</script>

<div class="flex h-screen overflow-hidden">
	<!-- Sidebar -->
	<aside class="hidden w-64 shrink-0 border-r border-primary/20 bg-surface dark:border-primary/20 dark:bg-surface-dark lg:block">
		<div class="flex h-full flex-col">
			<div data-logo class="flex items-center justify-center py-6">
				<img src="/img/arm-logo-black.png" alt="ARM" class="h-24 w-24 dark:hidden" />
				<img src="/img/arm-logo-white.png" alt="ARM" class="hidden h-24 w-24 dark:block" />
			</div>
			<hr class="border-primary/20 dark:border-primary/20" />
			<nav class="flex-1 space-y-1 px-3 py-4">
				{#each navItems as item}
					<a
						href={item.href}
						data-active={isActive(item.href, $page.url.pathname) || undefined}
						class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors
							{isActive(item.href, $page.url.pathname)
								? 'bg-primary-light-bg text-primary-text dark:bg-primary-light-bg-dark/30 dark:text-primary-text-dark'
								: 'text-gray-700 hover:bg-primary/10 dark:text-gray-300 dark:hover:bg-primary/15'}"
					>
						<svg class="h-5 w-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={item.icon} />
						</svg>
						{item.label}
					</a>
				{/each}
			</nav>
			<hr class="border-primary/20 dark:border-primary/20" />
			<SidebarStats systemInfo={$dashboard.system_info} systemStats={$dashboard.system_stats} transcoderInfo={$dashboard.transcoder_info} transcoderStats={$dashboard.transcoder_system_stats} armOnline={$dashboard.arm_online} transcoderOnline={$dashboard.transcoder_online} />
		</div>
	</aside>

	<!-- Main content -->
	<div class="flex flex-1 flex-col overflow-hidden">
		<!-- Top bar -->
		<header class="flex h-16 items-center justify-between border-b border-primary/20 bg-surface px-4 dark:border-primary/20 dark:bg-surface-dark lg:px-6">
			<button
				onclick={() => sidebarOpen = !sidebarOpen}
				aria-label="Toggle sidebar"
				class="rounded-lg p-2 text-gray-500 hover:bg-primary/10 dark:text-gray-400 dark:hover:bg-primary/15 lg:hidden"
			>
				<svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
				</svg>
			</button>

			<div class="flex items-center gap-4 ml-auto">
				<!-- Dark mode toggle -->
				<button
					onclick={toggleTheme}
					class="rounded-lg p-2 text-gray-500 hover:bg-primary/10 dark:text-gray-400 dark:hover:bg-primary/15"
				>
					{#if $theme === 'dark'}
						<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
						</svg>
					{:else}
						<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
						</svg>
					{/if}
				</button>
			</div>
		</header>

		<!-- Mobile sidebar overlay -->
		{#if sidebarOpen}
			<div class="fixed inset-0 z-40 lg:hidden">
				<button class="absolute inset-0 bg-black/50" aria-label="Close sidebar" onclick={() => sidebarOpen = false}></button>
				<aside class="relative z-50 flex h-full w-64 flex-col bg-surface shadow-xl dark:bg-surface-dark">
					<div data-logo class="flex items-center justify-center py-6">
						<img src="/img/arm-logo-black.png" alt="ARM" class="h-24 w-24 dark:hidden" />
						<img src="/img/arm-logo-white.png" alt="ARM" class="hidden h-24 w-24 dark:block" />
					</div>
					<hr class="border-primary/20 dark:border-primary/20" />
					<nav class="flex-1 space-y-1 px-3 py-4">
						{#each navItems as item}
							<a
								href={item.href}
								onclick={() => sidebarOpen = false}
								data-active={isActive(item.href, $page.url.pathname) || undefined}
								class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors
									{isActive(item.href, $page.url.pathname)
										? 'bg-primary-light-bg text-primary-text dark:bg-primary-light-bg-dark/30 dark:text-primary-text-dark'
										: 'text-gray-700 hover:bg-primary/10 dark:text-gray-300 dark:hover:bg-primary/15'}"
							>
								<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={item.icon} />
								</svg>
								{item.label}
							</a>
						{/each}
					</nav>
					<hr class="border-primary/20 dark:border-primary/20" />
					<SidebarStats systemInfo={$dashboard.system_info} systemStats={$dashboard.system_stats} transcoderInfo={$dashboard.transcoder_info} transcoderStats={$dashboard.transcoder_system_stats} armOnline={$dashboard.arm_online} transcoderOnline={$dashboard.transcoder_online} />
				</aside>
			</div>
		{/if}

		<!-- Page content -->
		<main class="flex-1 overflow-y-auto p-4 lg:p-6">
			{@render children()}
		</main>
	</div>
</div>
