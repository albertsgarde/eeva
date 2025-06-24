<script lang="ts">
	import { goto } from '$app/navigation';
	import FormQuestion from '$lib/FormQuestion.svelte';
	import SuccessButton from '$lib/ui/SuccessButton.svelte';
	import type { Data } from './+page.server';
	import { m } from '$loc/messages.js';
	import { FormResponse } from '$lib/base';
	import { debounce } from 'lodash-es';

	interface Props {
		data: Data;
	}
	let { data }: Props = $props();
	let { formResponseId, formResponse: initialFormResponse, maxExampleAnswers } = data;
	let formResponse = $state(structuredClone(initialFormResponse));

	let continuing: boolean = $state(false);

	async function saveToBackend(formResponse: FormResponse) {
		const url = `/api/form-responses/${formResponseId}`;
		await fetch(url, {
			method: `PUT`,
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(formResponse)
		}).then(async (response) => {
			if (!response.ok) {
				continuing = false;
				throw new Error('Network response was not ok: ' + (await response.text()));
			}
		});
	}

	async function submit() {
		continuing = true;
		await saveToBackend(formResponse).then(() => {
			goto(`/form-responses/${formResponseId}/completed`);
		});
	}

	const debouncedSave = debounce(saveToBackend, 1000);
</script>

<div class="mx-auto flex max-w-2xl flex-col">
	<div class="overflow-y-auto overflow-x-hidden p-1">
		{#each formResponse.responses as questionResponse, index}
			<FormQuestion
				bind:questionResponse={formResponse.responses[index]}
				onChange={(event) => {
					debouncedSave(formResponse);
				}}
				{maxExampleAnswers}
			/>
			<hr class="border-slate-600" />
		{/each}
		<div class="h-4"></div>
		<div class="flex items-center justify-end">
			<SuccessButton onClick={submit} processing={continuing}>{m.submit()}</SuccessButton>
		</div>
	</div>
</div>
