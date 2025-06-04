<script lang="ts">
	import type { Message } from './base';

	export let message: Message;
	export let subjectName: string;
</script>

{#if message.interviewer === false}
	<div class="flex flex-col items-end">
		<span class="text-xs text-gray-500"> {subjectName} </span>
		<div class="max-w-xl self-end rounded-lg rounded-tr-none bg-blue-500 p-3 text-white">
			{message.content}
		</div>
	</div>
{:else}
	<div class="flex flex-col">
		<span class="text-xs text-gray-500"> Interviewer </span>
		<div class="max-w-xl self-start rounded-lg rounded-tl-none bg-gray-200 p-3">
			{message.content}
		</div>
	</div>
{/if}
