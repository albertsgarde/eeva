<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}
	let { children }: Props = $props();
</script>

<h2 class="my-2 mt-4 text-xl font-semibold text-gray-100">
	{@render children()}
</h2>
