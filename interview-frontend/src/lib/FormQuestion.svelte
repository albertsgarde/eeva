<script lang="ts">
	export let question: string = '';
	export let examples: string[] = ['', '', '', ''];
</script>

<div class="mx-auto w-full max-w-2xl space-y-4 p-6">
	<h2 class="text-xl font-semibold text-gray-100">{question}</h2>
	<div class="grid grid-cols-2 gap-4">
		{#each examples as example}
			<div
				class="border-3 pointer-events-none cursor-default select-none rounded-lg border-gray-900 bg-gray-800 p-2.5 pt-2 text-gray-300"
			>
				{example}
			</div>
		{/each}
	</div>

	<textarea
		class="mt-4 w-full resize-none rounded-lg border border-gray-600 bg-gray-700 p-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
		rows="4"
		placeholder="Type your answer here..."
	></textarea>
</div>
