<script lang="ts">
	import FormQuestion from '$lib/FormQuestion.svelte';
	import type { Data } from './+page.server';

	export let data: Data;

	let { questions } = data;
</script>

<!--
	`mx-auto`: Centers the container horizontally.
	`max-w-[80ch]`: Sets a max-width for readability (80 characters).
	`max-h-[80vh]`: Sets a max-height relative to the viewport height.
	`overflow-y-auto`: Allows vertical scrolling if content overflows.
	`p-4`: Adds padding inside the container.
-->
<div class="mx-auto max-w-[80ch] overflow-y-auto">
	{#each questions as { id, question }}
		<FormQuestion {question} />
	{/each}
</div>
