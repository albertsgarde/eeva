<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		onClick: () => Promise<void>;
		disabled: boolean;
		children: Snippet;
	}
	let { onClick, disabled = false, children }: Props = $props();
</script>

<button
	class="m-0.5 rounded bg-green-600 px-4 py-2 font-bold text-white hover:bg-green-700 focus:outline-none active:bg-green-800 disabled:cursor-not-allowed disabled:bg-gray-600 disabled:opacity-50"
	onclick={onClick}
	{disabled}
>
	{@render children()}
</button>
