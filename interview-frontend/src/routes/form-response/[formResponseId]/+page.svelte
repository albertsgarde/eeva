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
		const url = `/api/form-response/${formResponseId}/subject-name`;
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
		const url = `/api/form-response/${formResponseId}/question/${questionIndex}`;
		await fetch(url, {
			method: `PUT`,
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(questionResponse)
		}).then(async (response) => {
			if (!response.ok) {
				formResponse.responses[questionIndex] = questionResponse; // revert to old response on error
				throw new Error('Network response was not ok: ' + (await response.text()));
			}
		});
	}
</script>

<div class="flex">
	<!-- Name input area -->
	<div class="w-1/3 p-4">
		<label for="userName" class="mb-2 block text-gray-200">Your Name</label>
		<input
			id="userName"
			type="text"
			bind:value={subjectName}
			placeholder="Enter your name"
			class="mb-2 mr-1 max-w-[60ch] rounded border border-gray-600 bg-gray-700 p-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
		/>
		<button
			on:click={saveSubjectName}
			class="rounded bg-green-600 px-4 py-2 font-bold text-white hover:bg-green-700 focus:outline-none active:bg-green-800 disabled:cursor-not-allowed disabled:bg-gray-600 disabled:opacity-50"
			disabled={subjectName === formResponse.subjectName}
		>
			Save Name
		</button>
	</div>

	<!-- Form questions scrollable div -->
	<div class="mx-auto w-1/3 max-w-[80ch] overflow-y-auto p-1">
		{#each formResponse.responses as questionResponse, index}
			<FormQuestion
				{questionResponse}
				onSave={(response: string) => saveResponse(response, index)}
			/>
		{/each}
	</div>
	<div class="w-1/3 p-4">
		<!-- Placeholder for additional content or actions -->
	</div>
</div>
