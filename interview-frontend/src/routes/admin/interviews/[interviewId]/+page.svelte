<script lang="ts">
	import type { InterviewId, Message } from '$lib/base';
	import ChatFrame from '$lib/ChatFrame.svelte';
	import ChatMessageContainer from '$lib/ChatMessageContainer.svelte';
	import MessageBubble from '$lib/MessageBubble.svelte';
	import type { Interview } from './+page.server.js';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import FolderOutput from '@lucide/svelte/icons/folder-output';

	export let data: { interviewId: InterviewId; interview: Interview };

	let { interviewId, interview } = data;

	let elemChat: ChatMessageContainer;

	let interviewerSystemPrompt: string = '';
	let suggestion: string = 'Suggestion will appear here';
	let activeUntil: number = -1;

	let previousPromptId: string = '';

	const curMessages: Message[] = interview.messages;
	const subjectName = interview.subjectName;

	function onPromptKeydown(event: KeyboardEvent) {
		if (['Enter'].includes(event.code)) {
			event.preventDefault();
			getSuggestion();
		}
	}

	async function loadPrompt(): Promise<void> {
		const promptId: string | null = await prompt('ID of system prompt to load:', previousPromptId);
		if (promptId === '') {
			alert('No prompt ID provided.');
			return;
		}
		if (!promptId) {
			return;
		}
		previousPromptId = promptId;
		const url = `/api/prompt/${promptId}`;
		const response = await fetch(url);
		if (!response.ok) {
			alert(`Error loading prompt: ${(await response.text()) || 'Unknown error'}`);
			return;
		}
		const data = await response.json();
		interviewerSystemPrompt = data.content;
	}

	async function getSuggestion(): Promise<void> {
		if (!interviewerSystemPrompt) {
			alert('Please enter a system prompt for the interviewer.');
			return;
		}
		const url = `/api/interview/${interviewId.id}/get_response_custom_prompt`;
		const message: Message = await fetch(url, {
			method: `POST`,
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				interviewerSystemPrompt,
				messageIndex: activeUntil == -1 ? null : activeUntil
			})
		}).then(async (response) => {
			if (!response.ok) {
				throw new Error('Network response was not ok: ' + (await response.text()));
			}
			return response.json();
		});
		suggestion = message.content;
	}
</script>

<div class="flex">
	<div class="w-1/4 p-4">
		<div class="flex flex-col">
			<div class="flex">
				<span class="my-auto text-xs text-gray-500">System prompt</span>
				<button
					class="bl-auto ml-auto rounded-md bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700"
					onclick={loadPrompt}
				>
					<FolderOutput />
				</button>
			</div>
			<textarea
				bind:value={interviewerSystemPrompt}
				placeholder="System prompt for interviewer... "
				class="flex-1 resize-none rounded-md border p-2 focus:outline-none"
				rows="20"
			></textarea>
		</div>

		<button
			class="rounded-md bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700"
			onclick={getSuggestion}
		>
			<RefreshCw />
		</button>
		<MessageBubble
			message={{
				content: suggestion,
				interviewer: true
			}}
			{subjectName}
		/>
	</div>
	<div class="w-1/2">
		<ChatFrame>
			<ChatMessageContainer
				bind:this={elemChat}
				messages={curMessages}
				{subjectName}
				{activeUntil}
				onBubbleClick={(index: number) => {
					activeUntil = index;
				}}
			/>
		</ChatFrame>
	</div>
</div>
