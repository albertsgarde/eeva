<script lang="ts">
	import type { FormResponseId } from '$lib/base';
	import Title from '$lib/ui/Title.svelte';
	import SuccessButton from '$lib/ui/SuccessButton.svelte';
	import { goto } from '$app/navigation';

	import { m } from '$loc/messages.js';
	import P from '$lib/ui/P.svelte';
	import Subtitle from '$lib/ui/Subtitle.svelte';
	import Markdown from '$lib/ui/Markdown.svelte';
	import { createFormResponse } from './utils';
	import type { Data } from './+page.server';

	interface Props {
		data: Data;
	}
	let { data }: Props = $props();
	let { formId, formResponseId } = data;

	let continuing: boolean = $state(false);
	let creatingNew: boolean = $state(false);

	async function handleContinue(): Promise<void> {
		continuing = true;
		goto(`/form-responses/${formResponseId}`);
	}

	// Function to handle form submission
	async function handleCreateNew(): Promise<void> {
		creatingNew = true;
		const formResponseId: FormResponseId = await createFormResponse(formId, fetch);
		goto(`/form-responses/${formResponseId}`);
	}
</script>

<div class="flex h-dvh items-center justify-center">
	<div class="mx-auto max-w-2xl px-4">
		<Subtitle>Vil du fortsætte din tidligere besvarelse?</Subtitle>
		<SuccessButton onClick={handleContinue} processing={continuing} disabled={creatingNew}
			>Fortsæt</SuccessButton
		>
		<SuccessButton onClick={handleCreateNew} processing={creatingNew} disabled={continuing}
			>Ny besvarelse</SuccessButton
		>
	</div>
</div>
