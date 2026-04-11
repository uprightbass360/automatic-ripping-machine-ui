<script lang="ts">
	import { posterSrc, posterFallback } from '$lib/utils/poster';

	interface Props {
		url: string | null | undefined;
		alt?: string;
		class?: string;
		style?: string;
	}

	let { url, alt = '', class: className = 'h-28 w-20 shrink-0 rounded-sm object-cover', style: styleStr = '' }: Props = $props();
</script>

<img
	src={posterSrc(url)}
	{alt}
	class={className}
	style={styleStr || undefined}
	loading="lazy"
	onerror={posterFallback}
/>
