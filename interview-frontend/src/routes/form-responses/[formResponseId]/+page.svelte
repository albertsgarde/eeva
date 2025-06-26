<script lang="ts">
	import { goto } from '$app/navigation';
	import FormQuestion from '$lib/FormQuestion.svelte';
	import SuccessButton from '$lib/ui/SuccessButton.svelte';
	import type { Data } from './+page.server';
	import { m } from '$loc/messages.js';
	import { FormResponse } from '$lib/base';
	import { debounce } from 'lodash-es';
	import InputText from '$lib/ui/InputText.svelte';
	import P from '$lib/ui/P.svelte';
	import Title from '$lib/ui/Title.svelte';
	import IconArrowDown from '@lucide/svelte/icons/arrow-down';

	interface Props {
		data: Data;
	}
	let { data }: Props = $props();
	let { formResponseId, formResponse: initialFormResponse, maxExampleAnswers, showEmail } = data;
	let formResponse = $state(structuredClone(initialFormResponse));

	let subjectEmail: string = $state(showEmail ? (initialFormResponse.subjectEmail ?? '') : '');

	let continuing: boolean = $state(false);

	let questionStart: HTMLElement | undefined;

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
		formResponse.subjectEmail = $state.snapshot(subjectEmail).trim();
		await saveToBackend(formResponse).then(() => {
			goto(`/form-responses/${formResponseId}/completed`);
		});
	}

	async function scrollToQuestions() {
		questionStart?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	const debouncedSave = debounce(saveToBackend, 1000);
</script>

<div class="mx-auto flex max-w-2xl flex-col">
	<div class="mt-8 overflow-y-auto overflow-x-hidden">
		<Title>{m['page.forms.title']()}</Title>
		<!--<Subtitle>{m['page.forms.subtitle']()}</Subtitle>-->
		<div class="h-2"></div>
		<P>{m['page.forms.pitch']()}</P>

		<div class="items-right flex justify-end">
			<SuccessButton onClick={scrollToQuestions}><IconArrowDown /></SuccessButton>
		</div>
		<hr bind:this={questionStart} class="my-12 border-slate-600" />
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
		<P>Email (optional):</P>
		<div class="flex items-center justify-end">
			<InputText placeholder="Your email..." bind:response={subjectEmail}></InputText>
			<SuccessButton onClick={submit} processing={continuing}>{m.submit()}</SuccessButton>
		</div>
		<P
			>Hvis du får en invitation, er du selvfølgelig meget velkommen til at takke nej, men overvej
			at vi specifikt har inviteret dig fordi vi tror du vil trives i de andre deltageres selskab.</P
		>
		<div class="my-4"></div>
	</div>
</div>
