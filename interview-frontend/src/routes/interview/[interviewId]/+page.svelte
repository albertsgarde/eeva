<script lang="ts">
	import type { InterviewId, Message } from '$lib/base';
	import ChatMessageContainer from '$lib/ChatMessageContainer.svelte';
	import ChatInput from '$lib/ChatInput.svelte';
	import ChatFrame from '$lib/ChatFrame.svelte';
	import type { Interview } from './+page.server';

	export let data: { interviewId: InterviewId, interview: Interview};

	let {subjectName, messages} = data.interview;

	let elemChat: ChatMessageContainer;

	let interviewId: InterviewId = data.interviewId;
	let curMessages: Message[] = messages;

	function scrollToBottom(behavior?: 'auto' | 'instant' | 'smooth') {
		elemChat.scrollToBottom(behavior);
	}

	async function getResponse(userMessage: string): Promise<Message[]> {
		const url = `/api/interview/${interviewId.id}/respond`;
		const messages = await fetch(url, {
			method: `POST`,
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				userMessage: userMessage
			})
		}).then(async (response) => {
			if (!response.ok) {
				throw new Error('Network response was not ok: ' + (await response.text()));
			}
			return response.json();
		});
		return messages;
	}

	async function addMessage(messageText: string): Promise<void> {
		const userMessage = {
			interviewer: false,
			content: messageText
		};
		// Update the message feed
		curMessages = [...curMessages, userMessage];

		// Smooth scroll to bottom
		// Timeout prevents race condition
		setTimeout(() => scrollToBottom('smooth'), 0);

		getResponse(messageText).then((messages) => {
			curMessages = messages;

			setTimeout(() => scrollToBottom('smooth'), 0);
		});
	}
</script>

<!-- Body -->
<ChatFrame>
	<ChatMessageContainer bind:this={elemChat} messages={curMessages} subjectName="You" />
	<ChatInput sendMessage={addMessage} />
</ChatFrame>
