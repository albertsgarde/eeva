<script lang="ts">
	import { goto } from '$app/navigation';
	import FormQuestion from '$lib/FormQuestion.svelte';
	import SuccessButton from '$lib/ui/SuccessButton.svelte';
	import type { Data } from './+page.server';
	import { m } from '$loc/messages.js';

	interface Props {
		data: Data;
	}
	let { data }: Props = $props();
	let { formResponseId, formResponse: initialFormResponse, maxExampleAnswers } = data;
	let formResponse = $state(structuredClone(initialFormResponse));

	let continuing: boolean = $state(false);

	async function submit() {
		const url = `/api/form-responses/${formResponseId}`;
		continuing = true;
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
			goto(`/form-responses/${formResponseId}/completed`);
		});
	}
</script>

<div class="mx-auto flex max-w-2xl flex-col">
	<div class="overflow-y-auto overflow-x-hidden p-1">
		{#each formResponse.responses as questionResponse, index}
			<FormQuestion bind:questionResponse={formResponse.responses[index]} {maxExampleAnswers} />
			<hr class="border-slate-600" />
		{/each}
		<div class="h-4"></div>
		<div class="flex items-center justify-end">
			<SuccessButton onClick={submit} processing={continuing}>{m.submit()}</SuccessButton>
		</div>
	</div>
</div>
