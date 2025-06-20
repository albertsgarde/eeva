<script lang="ts">
	import type { QuestionResponse } from '$lib/base';
	import FormQuestion from '$lib/FormQuestion.svelte';
	import type { Data } from './+page.server';

	export let data: Data;
	let { formResponseId, formResponse } = data;
	let subjectName: string = formResponse.subjectName;

	async function saveSubjectName() {
		const oldSubjectName = formResponse.subjectName;
		formResponse = { ...formResponse, subjectName };
		const url = `/api/form-responses/${formResponseId}/subject-name`;
		await fetch(url, {
			method: 'PUT',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(formResponse.subjectName)
		}).then(async (response) => {
			if (!response.ok) {
				formResponse = { ...formResponse, subjectName: oldSubjectName };
				throw new Error('Network response was not ok: ' + (await response.text()));
			}
		});
	}

	async function saveResponse(subjectResponse: string, questionIndex: number) {
		let questionResponse: QuestionResponse = formResponse.responses[questionIndex];
		const oldResponse = questionResponse.response;

		formResponse.responses[questionIndex] = { ...questionResponse, response: subjectResponse };
		const url = `/api/form-responses/${formResponseId}/question/${questionIndex}`;
		await fetch(url, {
			method: `PUT`,
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(formResponse.responses[questionIndex])
		}).then(async (response) => {
			if (!response.ok) {
				formResponse.responses[questionIndex] = questionResponse; // revert to old response on error
				throw new Error('Network response was not ok: ' + (await response.text()));
			}
		});
	}
</script>

<div class="mx-auto flex max-w-2xl flex-col">
	<div class="overflow-y-auto p-1">
		{#each formResponse.responses as questionResponse, index}
			<FormQuestion
				{questionResponse}
				onSave={(response: string) => saveResponse(response, index)}
			/>
		{/each}
	</div>
</div>
