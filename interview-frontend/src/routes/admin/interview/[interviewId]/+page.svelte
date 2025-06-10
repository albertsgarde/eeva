<script lang="ts">
	import type { InterviewId, Message } from '$lib/base';
	import ChatFrame from '$lib/ChatFrame.svelte';
	import ChatMessageContainer from '$lib/ChatMessageContainer.svelte';
	import MessageBubble from '$lib/MessageBubble.svelte';
	import type { Interview } from './+page.server.js';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';

	export let data: { interviewId: InterviewId; interview: Interview };

	let { interviewId, interview } = data;

	let elemChat: ChatMessageContainer;

	let interviwerSystemPromptId: string = '';
	let suggestion: string = 'Suggestion will appear here';
	let activeUntil: number = -1;

	const curMessages: Message[] = interview.messages;
	const subjectName = interview.subjectName;

	function onPromptKeydown(event: KeyboardEvent) {
		if (['Enter'].includes(event.code)) {
			event.preventDefault();
			getSuggestion();
		}
	}

	async function getSuggestion(): Promise<void> {
		if (!interviwerSystemPromptId) {
			alert('Please enter a system prompt ID for the interviewer.');
			return;
		}
		const url = `/api/interview/${interviewId.id}/get_response?interviewerSystemPromptId=${interviwerSystemPromptId}&messageIndex=${activeUntil == -1 ? null : activeUntil}`;
		const message: Message = await fetch(url, {
			method: `GET`
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
		<div class="flex">
			<input
				bind:value={interviwerSystemPromptId}
				type="text"
				placeholder="System prompt id for interviewer..."
				class="flex-1 border focus:outline-none"
				onkeypress={onPromptKeydown}
			/>
			<button
				class="bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700"
				onclick={getSuggestion}
			>
				<RefreshCw />
			</button>
		</div>
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
