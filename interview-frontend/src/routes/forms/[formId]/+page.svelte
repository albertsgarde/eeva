<script lang="ts">
	import type { FormResponseId } from '$lib/base';
	import Header2 from '$lib/ui/Header2.svelte';
	import InputText from '$lib/ui/InputText.svelte';
	import SuccessButton from '$lib/ui/SuccessButton.svelte';
	import type { Data } from './+page.server';
	import { goto } from '$app/navigation';

	import { m } from '$loc/messages.js';

	interface Props {
		data: Data;
	}
	let { data }: Props = $props();
	let { formId } = data;

	// State to store the user's name
	let userName: string = $state('');

	let continuing: boolean = $state(false);

	// Function to handle form submission
	async function handleContinue(): Promise<void> {
		const createFormResponseRequest = {
			formId,
			subjectName: userName.trim()
		};

		continuing = true;
		const { id: formResponseId }: { id: FormResponseId } = await fetch(
			`/api/form-responses/create-from-form`,
			{
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(createFormResponseRequest)
			}
		).then(async (response) => {
			if (response.status !== 200) {
				const responseText = await response.text();
				continuing = false;
				throw new Error('Failed to create form response: ' + responseText);
			}
			return response.json();
		});
		goto(`/form-responses/${formResponseId}`);
	}
</script>

<div class="flex h-dvh items-center justify-center">
	<div class="mx-auto max-w-2xl px-4">
		<P>{m['page.forms.pitch']()}</P>
		<Header2>{m['page.forms.pleaseInputName']()}</Header2>

		<div class="flex">
			<InputText
				bind:response={userName}
				placeholder={m['page.forms.namePlaceholder']()}
				onEnter={handleContinue}
			/>
			<SuccessButton onClick={handleContinue} disabled={!userName.trim()} processing={continuing}>
				{m['page.forms.continue']()}
			</SuccessButton>
		</div>
	</div>
</div>
