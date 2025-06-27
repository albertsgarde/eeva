<script lang="ts">
	import Header2 from '$lib/ui/Header2.svelte';
	import P from '$lib/ui/P.svelte';
	import SuccessButton from '$lib/ui/SuccessButton.svelte';
	import type { Data } from './+page.server';
	import { m } from '$loc/messages.js';
	import { browser } from '$app/environment';

	interface Props {
		data: Data;
	}
	const { data }: Props = $props();
	const { formResponseId } = data;

	let host = $derived(() => {
		if (browser) {
			return location.host;
		} else {
			return '';
		}
	});

	const link = $derived(() => `${host()}/form-responses/${formResponseId}`);

	async function copyLink() {
		await navigator.clipboard.writeText(link());
	}
</script>

<div class="flex h-dvh items-center justify-center">
	<div class="flex max-w-xl flex-col px-4">
		<div class=" items-center text-center">
			<Header2>{m['page.formResponses/completed.title']()}</Header2>
		</div>
		<P>
			{m['page.formResponses/completed.description']({
				url: `${host()}/form-responses/${formResponseId}`
			})}
		</P>
		<SuccessButton onClick={copyLink}>{m[`page.formResponses/completed.copyLink`]()}</SuccessButton>
		<a class="text-xs" href={link()}>{link()}</a>

		<div class="h-12"></div>
		<P>Hvis du er interesseret i projektet og gerne vil høre mere kan du kontakte os på email.</P>
		<div class="">
			<P>Abel: abeljordbo@gmail.com</P>
			<P>Albert: albertsgarde@gmail.com</P>
		</div>
	</div>
</div>
