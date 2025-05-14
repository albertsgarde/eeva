<script lang="ts">
	import IconSend from '@lucide/svelte/icons/send-horizontal';
	import { OpenAI } from 'openai';

	export let data: {
		startMessage: string;
		interviewerPrompt: string;
	};

	interface Message {
		host: boolean;
		name: string;
		message: string;
		color: string;
	}

	let elemChat: HTMLElement;

	// Messages
	let messageFeed: Message[] = [
		{
			host: false,
			name: 'Interviewer',
			message: data.startMessage,
			color: 'preset-tonal-primary'
		}
	];
	let currentMessage = '';

	let previousResponseId: string | null = null;

	// Use a throwaway api key that only has access to $0.1 each month. Should obviously be done in a better way in future.
	const client = new OpenAI({
		apiKey:
			'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',
		dangerouslyAllowBrowser: true
	});

	function scrollChatBottom(behavior?: 'auto' | 'instant' | 'smooth') {
		elemChat.scrollTo({ top: elemChat.scrollHeight, behavior });
	}

	async function getResponse(
		userMessage: string,
		previousResponseId: string | null
	): Promise<{ message: string; id: string }> {
		const response = await client.responses
			.create({
				model: 'gpt-4o-mini',
				input: [
					{
						role: 'developer',
						content: data.interviewerPrompt
					},
					{
						role: 'user',
						content: userMessage
					}
				],
				previous_response_id: previousResponseId
			})
			.then((response) => {
				const responseId = response.id;
				const message = response.output_text;

				return { message, id: responseId };
			});
		return response;
	}

	function addMessage() {
		if (!currentMessage) return;
		const userMessage = currentMessage;
		currentMessage = '';

		const newMessage = {
			host: true,
			name: 'User',
			message: userMessage,
			color: 'preset-tonal-primary'
		};
		// Update the message feed
		messageFeed = [...messageFeed, newMessage];

		// Smooth scroll to bottom
		// Timeout prevents race condition
		setTimeout(() => scrollChatBottom('smooth'), 0);

		getResponse(userMessage, previousResponseId)
			.then(({ message, id }) => {
				previousResponseId = id;
				const newMessage = {
					host: false,
					name: 'You',
					message: message,
					color: 'preset-tonal-secondary'
				};
				// Update the message feed
				messageFeed = [...messageFeed, newMessage];

				setTimeout(() => scrollChatBottom('smooth'), 0);
			})
			.then(() => {
				// Save the conversation
				const conversationName = 'albert-test1';
				saveConversation(conversationName, messageFeed);
			});
	}

	async function saveConversation(conversation_name: string, conversation: Message[]) {
		const url = `/api/save_conversation`;
		await fetch(url, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ conversation_name: conversation_name, conversation: conversation })
		});
	}

	function onPromptKeydown(event: KeyboardEvent) {
		if (['Enter'].includes(event.code)) {
			event.preventDefault();
			addMessage();
		}
	}
</script>

<!-- Body -->
<div class="flex h-screen items-center justify-center bg-gray-100 p-4">
	<!-- Main Chat Container -->
	<div class="h-256 flex w-full max-w-screen-xl flex-col rounded-lg bg-white shadow-md">
		<!-- Chat Header -->
		<div class="rounded-t-lg bg-blue-600 p-4 text-white">
			<h1 class="text-xl font-bold">Identity</h1>
		</div>
		<!-- Chat Messages Container -->
		<div bind:this={elemChat} class="flex-1 space-y-4 overflow-y-auto p-4">
			{#each messageFeed as bubble}
				{#if bubble.host === true}
					<div class="flex flex-col items-end">
						<span class="text-xs text-gray-500">
							{bubble.name}
						</span>
						<div class="max-w-xl self-end rounded-lg rounded-tr-none bg-blue-500 p-3 text-white">
							{bubble.message}
						</div>
					</div>
				{:else}
					<div class="flex flex-col">
						<span class="text-xs text-gray-500">
							{bubble.name}
						</span>
						<div class="max-w-xl self-start rounded-lg rounded-tl-none bg-gray-200 p-3">
							{bubble.message}
						</div>
					</div>
				{/if}
			{/each}
		</div>
		<!-- Chat Input Area -->
		<div class="border-t p-4">
			<div class="flex">
				<input
					bind:value={currentMessage}
					type="text"
					placeholder="Type your message..."
					class="flex-1 rounded-l-lg border px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
					onkeypress={onPromptKeydown}
				/>
				<button
					class="rounded-r-lg bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700"
					onclick={addMessage}
				>
					<IconSend />
				</button>
			</div>
		</div>
	</div>
</div>
