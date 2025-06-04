<script lang="ts">
	import type { CreateInterviewRequest, InterviewId, Message } from '$lib/base';
	import type { PageData } from './+page';
	import { onMount } from 'svelte';
	import ChatMessageContainer from '$lib/ChatMessageContainer.svelte';
	import ChatInput from '$lib/ChatInput.svelte';
	import ChatFrame from '$lib/ChatFrame.svelte';

	export let data: PageData;

	let { startMessageId, interviewerPromptId, subjectName: querySubjectName } = data;

	let elemChat: ChatMessageContainer;

	let interviewId: InterviewId;
	let curMessages: Message[] = [];

	onMount(async () => {
		const subjectName = getSubjectName(querySubjectName);

		const response = await createInterview(startMessageId, interviewerPromptId, subjectName);
		interviewId = response.interviewId;
		curMessages = response.messages;
	});

	function getSubjectName(querySubjectName: string | undefined): string {
		if (querySubjectName !== undefined) {
			return querySubjectName;
		} else {
			let subjectName = null;
			while (subjectName === null) {
				subjectName = prompt('What is your name?');
			}
			return subjectName;
		}
	}

	async function createInterview(
		startMessageId: string,
		interviewerPromptId: string,
		subjectName: string
	): Promise<{ interviewId: InterviewId; messages: Message[] }> {
		const createInterviewRequest: CreateInterviewRequest = {
			startMessageId: startMessageId,
			interviewerSystemPromptId: interviewerPromptId,
			subjectName: subjectName
		};

		const response: { interviewId: InterviewId; messages: Message[] } = await fetch(
			`/api/interview`,
			{
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(createInterviewRequest)
			}
		).then(async (response) => {
			if (response.status !== 200) {
				const responseText = await response.text();
				throw new Error('Failed to create interview: ' + responseText);
			}
			return response.json();
		});
		return response;
	}

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
