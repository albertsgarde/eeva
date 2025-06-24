<script lang="ts">
	import type { QuestionResponse } from './base';
	import Header2 from './ui/Header2.svelte';
	import InputMultiline from './ui/InputTextMultiline.svelte';
	import Markdown from './ui/Markdown.svelte';
	import { m } from '$loc/messages.js';

	interface Props {
		questionResponse: QuestionResponse;
		maxExampleAnswers: number | null;
	}
	let { questionResponse = $bindable(), maxExampleAnswers }: Props = $props();
</script>

<Header2>
	<Markdown content={questionResponse.question.question} />
</Header2>

<InputMultiline
	bind:response={questionResponse.response}
	numRows={6}
	placeholder={m['component.formQuestion.responsePlaceholder']()}
/>

<h3 class="text-l bg-gray-800 font-semibold text-gray-300">
	{m['component.formQuestion.examplesHeader']()}
</h3>
{#each questionResponse.question.exampleAnswers.slice(0, maxExampleAnswers ?? undefined) as example, index}
	<div
		class="pointer-events-none my-3 cursor-default select-none rounded-lg bg-gray-800 text-gray-300"
	>
		<div>
			<p class="text-sm text-gray-400">
				{m['component.formQuestion.exampleHeader']({ index: index + 1 })}
			</p>
		</div>
		{example}
	</div>
{/each}
