<script lang="ts">
	import type { QuestionResponse } from './base';

	export let questionResponse: QuestionResponse;
	export let onSave: (response: string) => Promise<void>;

	async function handleSave() {
		await onSave(response);
		questionResponse = { ...questionResponse, response };
	}

	let response: string = questionResponse.response;
</script>

<h2 class="text-xl font-semibold text-gray-100">{questionResponse.question.question}</h2>
<div class="grid grid-cols-2 gap-4">
	{#each questionResponse.question.exampleAnswers as example, index}
		<div
			class="pointer-events-none cursor-default select-none rounded-lg bg-gray-800 p-2.5 pt-2 text-gray-300"
		>
			<div>
				<p class="text-sm text-gray-400">Example {index + 1}:</p>
			</div>
			{example}
		</div>
	{/each}
</div>

<textarea
	bind:value={response}
	class="my-2 w-full resize-none rounded-lg border border-gray-600 bg-gray-700 p-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
	rows="6"
	placeholder="Type your answer here..."
></textarea>

<button
	class="rounded bg-green-600 px-4 py-2 font-bold text-white hover:bg-green-700 focus:outline-none active:bg-green-800 disabled:cursor-not-allowed disabled:bg-gray-600 disabled:opacity-50"
	onclick={handleSave}
	disabled={response === questionResponse.response}
>
	Save
</button>
