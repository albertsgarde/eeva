<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		onClick?: () => Promise<void>;
		disabled?: boolean;
		processing?: boolean;
		children: Snippet;
	}
	let {
		onClick = async () => {},
		disabled = false,
		processing = false,
		children
	}: Props = $props();
</script>

<button
	class="m-0.5 rounded bg-green-600 px-4 py-2 font-bold text-white hover:bg-green-700 focus:outline-none active:bg-green-800 disabled:cursor-not-allowed disabled:bg-gray-600 disabled:opacity-50"
	onclick={onClick}
	disabled={disabled || processing}
>
	{#if processing}
		<!-- Tailwind’s animate-spin does the rotating -->
		<svg
			class="h-5 w-5 animate-spin"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="2"
		>
			<!-- ghost ring -->
			<circle cx="12" cy="12" r="10" stroke-opacity="0.25" />
			<!-- arc -->
			<path d="M22 12a10 10 0 0 1-10 10" stroke-linecap="round" />
		</svg>
		<span class="sr-only">Loading…</span>
		<!-- screen-reader hint -->
	{:else}
		{@render children()}
	{/if}
</button>
