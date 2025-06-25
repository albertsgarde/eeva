<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}
	let { children }: Props = $props();
</script>

<h1 class="my-2 mt-4 text-justify text-lg font-semibold text-gray-100">
	{@render children()}
</h1>
