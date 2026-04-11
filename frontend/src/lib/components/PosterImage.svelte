<script lang="ts">
	import { posterSrc, posterFallback } from '$lib/utils/poster';

	interface Props {
		url: string | null | undefined;
		alt?: string;
		class?: string;
	}

	let { url, alt = '', class: className = 'h-28 w-20 shrink-0 rounded-sm object-cover' }: Props = $props();
</script>

<img
	src={posterSrc(url)}
	{alt}
	class={className}
	loading="lazy"
	onerror={posterFallback}
/>
