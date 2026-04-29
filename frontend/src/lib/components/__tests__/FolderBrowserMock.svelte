<script lang="ts">
	interface Props {
		onselect: (path: string) => void;
	}
	let { onselect }: Props = $props();
</script>

<button type="button" data-testid="folder-browser-mock-select" onclick={() => onselect('/home/arm/ingress/Movie_Folder')}>
	Mock select folder
</button>
