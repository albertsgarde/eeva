<script lang="ts">
	import type { InterviewId, Message } from '$lib/base';
	import ChatMessageContainer from '$lib/ChatMessageContainer.svelte';
	import ChatInput from '$lib/ChatInput.svelte';
	import ChatFrame from '$lib/ChatFrame.svelte';
	import type { Interview } from './+page.server';
	import { onMount } from 'svelte';

	export let data: { interviewId: InterviewId; interview: Interview };

	let { subjectName, messages } = data.interview;

	let elemChat: ChatMessageContainer;

	let interviewId: InterviewId = data.interviewId;
	let curMessages: Message[] = messages;

	function scrollToBottom(behavior?: 'auto' | 'instant' | 'smooth') {
		setTimeout(() => elemChat.scrollToBottom(behavior), 0);
	}

	onMount(() => {
		const interviewStream = new EventSource(`/api/interview/${interviewId.id}/stream`);

		function onMessage(ev: MessageEvent) {
			const interview = JSON.parse(ev.data);
			curMessages = interview.messages;
			scrollToBottom('smooth');
		}
		interviewStream.onmessage = onMessage;

		// Scroll to bottom on mount
		scrollToBottom('smooth');
	});

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
		scrollToBottom('smooth');

		getResponse(messageText);
		/*.then((messages) => {
			curMessages = messages;

			setTimeout(() => scrollToBottom('smooth'), 0);
		});*/
	}
</script>

<!-- Body -->
<ChatFrame>
	<ChatMessageContainer bind:this={elemChat} messages={curMessages} subjectName="You" />
	<ChatInput sendMessage={addMessage} />
</ChatFrame>
