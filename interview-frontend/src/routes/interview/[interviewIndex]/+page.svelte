<script lang="ts">
	import type { Message } from '$lib/base';
	import type { Interview } from './+page.server.ts';

	export let data: { interview: Interview };

	let { interview } = data;

	let elemChat: HTMLElement;

	const curMessages: Message[] = interview.messages;
	const subjectName = interview.subjectName;
</script>

<!-- Body -->
<div class="flex h-dvh items-center justify-center bg-gray-100 p-4">
	<!-- Main Chat Container -->
	<div class="w-256 flex h-[95vh] max-h-[95vh] max-w-[95vw] flex-col rounded-lg bg-white shadow-md">
		<!-- Chat Header -->
		<div class="rounded-t-lg bg-blue-600 p-4 text-white">
			<h1 class="text-xl font-bold">Eeva</h1>
		</div>
		<!-- Chat Messages Container -->
		<div bind:this={elemChat} class="flex-1 space-y-4 overflow-y-auto p-4">
			{#each curMessages as message}
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
			{/each}
		</div>
	</div>
</div>
