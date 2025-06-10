<script lang="ts">
	import type { Message } from './base';

	export let message: Message;
	export let subjectName: string;
	export let active: boolean = true;

	export let onClick: () => void = () => {};
</script>

{#if message.interviewer === false}
	<div class="flex flex-col items-end">
		<span class="text-xs text-gray-500"> {subjectName} </span>
		<button
			onclick={onClick}
			class="max-w-xl self-end rounded-lg rounded-tr-none text-left {active
				? 'bg-blue-500'
				: 'bg-blue-200'} p-3 text-white"
		>
			{message.content}
		</button>
	</div>
{:else}
	<div class="flex flex-col">
		<span class="text-xs text-gray-500"> Interviewer </span>
		<button
			onclick={onClick}
			class="max-w-xl self-start rounded-lg rounded-tl-none text-left {active
				? 'bg-gray-200'
				: 'bg-gray-100 text-gray-500'} p-3"
		>
			{message.content}
		</button>
	</div>
{/if}
