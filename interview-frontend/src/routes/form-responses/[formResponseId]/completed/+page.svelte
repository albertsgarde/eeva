<script lang="ts">
	import Header2 from '$lib/ui/Header2.svelte';
	import P from '$lib/ui/P.svelte';
	import SuccessButton from '$lib/ui/SuccessButton.svelte';
	import type { Data } from './+page.server';

	interface Props {
		data: Data;
	}
	const { data }: Props = $props();
	const { formResponseId } = data;

	async function copyLink() {
		const url = `${location.origin}/form-responses/${formResponseId}`;
		await navigator.clipboard.writeText(url);
	}
</script>

<div class="flex h-dvh items-center justify-center">
	<div class="mx-auto flex max-w-xl flex-col items-center px-4 text-center">
		<Header2>Tusind tak!</Header2>
		<P>
			Din besvarelse er blevet gemt. Hvis du senere ønsker at ændre din besvarelse, kan du benytte
			linket nedenfor.
		</P>
		<SuccessButton onClick={copyLink}>Kopier link</SuccessButton>
	</div>
</div>
