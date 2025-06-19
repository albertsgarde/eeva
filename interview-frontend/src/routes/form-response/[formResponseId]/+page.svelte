<script lang="ts">
	import type { QuestionResponse } from '$lib/base';
	import FormQuestion from '$lib/FormQuestion.svelte';
	import type { Data } from './+page.server';

	export let data: Data;

	let { formResponseId, formResponse } = data;

	async function saveResponse(questionIndex: number) {
		const url = `/api/form-response/${formResponseId}/question/${questionIndex}`;
		await fetch(url, {
			method: `PUT`,
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(formResponse.responses[questionIndex])
		}).then(async (response) => {
			if (!response.ok) {
				throw new Error('Network response was not ok: ' + (await response.text()));
			}
		});
	}
</script>

<div class="mx-auto max-w-[80ch] overflow-y-auto p-1">
	{#each formResponse.responses as questionResponse, index}
		<FormQuestion {questionResponse} onSave={() => saveResponse(index)} />
	{/each}
</div>
