<script lang="ts">
	import type { QuestionResponse } from './base';
	import SuccessButton from './ui/SuccessButton.svelte';

	export let questionResponse: QuestionResponse;
	export let onSave: (response: string) => Promise<void>;
	export let maxExampleAnswers: number | null = null;

	async function handleSave() {
		await onSave(response);
		questionResponse = { ...questionResponse, response };
	}

	let response: string = questionResponse.response;
</script>

<h2 class="text-xl font-semibold text-gray-100">{questionResponse.question.question}</h2>
{#each questionResponse.question.exampleAnswers.slice(0, maxExampleAnswers ?? undefined) as example, index}
	<div
		class="pointer-events-none cursor-default select-none rounded-lg bg-gray-800 p-2.5 pt-2 text-gray-300"
	>
		<div>
			<p class="text-sm text-gray-400">Example {index + 1}:</p>
		</div>
		{example}
	</div>
{/each}

<textarea
	bind:value={response}
	class="my-1 w-full resize-none rounded-lg border border-gray-600 bg-gray-700 p-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
	rows="6"
	placeholder="Type your answer here..."
></textarea>

<SuccessButton onClick={handleSave} disabled={response === questionResponse.response}>
	Save
</SuccessButton>
