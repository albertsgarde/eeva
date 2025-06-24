<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}
	let { children }: Props = $props();
</script>

<p class="m-0.5 whitespace-pre-line text-gray-100">
	{@render children()}
</p>
