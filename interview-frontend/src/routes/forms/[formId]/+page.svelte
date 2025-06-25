<script lang="ts">
	import type { FormResponseId } from '$lib/base';
	import Title from '$lib/ui/Title.svelte';
	import InputText from '$lib/ui/InputText.svelte';
	import SuccessButton from '$lib/ui/SuccessButton.svelte';
	import type { Data } from './+page.server';
	import { goto } from '$app/navigation';

	import { m } from '$loc/messages.js';
	import P from '$lib/ui/P.svelte';
	import Header2 from '$lib/ui/Header2.svelte';
	import Subtitle from '$lib/ui/Subtitle.svelte';
	import PSmall from '$lib/ui/PSmall.svelte';
	import Markdown from '$lib/ui/Markdown.svelte';

	interface Props {
		data: Data;
	}
	let { data }: Props = $props();
	let { formId } = data;

	let continuing: boolean = $state(false);

	// Function to handle form submission
	async function handleContinue(): Promise<void> {
		const createFormResponseRequest = {
			formId,
			subjectName: ''
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
		<Title>{m['page.forms.title']()}</Title>
		<Subtitle>{m['page.forms.subtitle']()}</Subtitle>
		<div class="h-2"></div>
		<P><Markdown content={m['page.forms.pitch']()} /></P>

		<div class="h-2"></div>
		<div class="flex justify-center">
			<SuccessButton onClick={handleContinue} processing={continuing}>
				{m['page.forms.continue']()}
			</SuccessButton>
		</div>
		<!--<details class="rounded p-4">
			<summary class="cursor-pointer select-none font-medium">Om produktet</summary>
			{m['page.forms.aboutTheApp']()}
		</details>-->
	</div>
</div>
