<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}
	let { children }: Props = $props();
</script>

<div class="flex h-dvh items-center justify-center p-4">
	<div class="w-256 flex h-[95vh] max-h-[95vh] max-w-[95vw] flex-col rounded-lg bg-white shadow-md">
		<!-- Chat Header -->
		<div class="rounded-t-lg bg-blue-600 p-4 text-white">
			<h1 class="text-xl font-bold">Eeva</h1>
		</div>
		{@render children()}
	</div>
</div>
