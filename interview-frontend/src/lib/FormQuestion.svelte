<script lang="ts">
	import type { QuestionResponse } from './base';
	import Header2 from './ui/Header2.svelte';
	import InputMultiline from './ui/InputTextMultiline.svelte';
	import Markdown from './ui/Markdown.svelte';
	import SuccessButton from './ui/SuccessButton.svelte';

	interface Props {
		questionResponse: QuestionResponse;
		onSave: (response: string) => Promise<void>;
		maxExampleAnswers: number | null;
	}
	let { questionResponse, onSave, maxExampleAnswers }: Props = $props();

	async function handleSave() {
		await onSave(response);
		questionResponse = { ...questionResponse, response };
	}

	let response: string = $state(questionResponse.response);
</script>

<Header2>
	<Markdown content={questionResponse.question.question} />
</Header2>

<InputMultiline bind:response numRows={6} placeholder="Type your answer here..." />

<SuccessButton onClick={handleSave} disabled={response === questionResponse.response}>
	Save
</SuccessButton>
<h3 class="text-l bg-gray-800 font-semibold text-gray-300">Examples for inspiration:</h3>
{#each questionResponse.question.exampleAnswers.slice(0, maxExampleAnswers ?? undefined) as example, index}
	<div
		class="pointer-events-none my-3 cursor-default select-none rounded-lg bg-gray-800 text-gray-300"
	>
		<div>
			<p class="text-sm text-gray-400">Example {index + 1}</p>
		</div>
		{example}
	</div>
{/each}
