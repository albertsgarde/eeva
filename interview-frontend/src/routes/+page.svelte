<script lang="ts">
	import IconSend from '@lucide/svelte/icons/send-horizontal';
	import type { InterviewId, Message } from './+page';

	export let data: { interviewId: InterviewId; messages: Message[] };

	let { interviewId, messages: cur_messages } = data;

	let elemChat: HTMLElement;

	let currentMessage = '';

	function scrollChatBottom(behavior?: 'auto' | 'instant' | 'smooth') {
		elemChat.scrollTo({ top: elemChat.scrollHeight, behavior });
	}

	async function getResponse(userMessage: string): Promise<Message[]> {
		const url = `/api/interview/${data.interviewId.id}/respond`;
		const messages = await fetch(url, {
			method: `POST`,
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				message: userMessage
			})
		}).then(async (response) => {
			if (!response.ok) {
				throw new Error('Network response was not ok: ' + (await response.text()));
			}
			return response.json();
		});
		return messages;
	}

	function addMessage() {
		if (!currentMessage) return;
		const userMessageText = currentMessage;
		currentMessage = '';

		const userMessage = {
			interviewer: false,
			content: userMessageText
		};
		// Update the message feed
		cur_messages = [...cur_messages, userMessage];

		// Smooth scroll to bottom
		// Timeout prevents race condition
		setTimeout(() => scrollChatBottom('smooth'), 0);

		getResponse(userMessageText).then((messages) => {
			cur_messages = messages;

			setTimeout(() => scrollChatBottom('smooth'), 0);
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
<div class="flex h-dvh items-center justify-center bg-gray-100 p-4">
	<!-- Main Chat Container -->
	<div class="w-256 flex h-[95vh] max-h-[95vh] max-w-[95vw] flex-col rounded-lg bg-white shadow-md">
		<!-- Chat Header -->
		<div class="rounded-t-lg bg-blue-600 p-4 text-white">
			<h1 class="text-xl font-bold">Eeva</h1>
		</div>
		<!-- Chat Messages Container -->
		<div bind:this={elemChat} class="flex-1 space-y-4 overflow-y-auto p-4">
			{#each cur_messages as message}
				{#if message.interviewer === false}
					<div class="flex flex-col items-end">
						<span class="text-xs text-gray-500"> You </span>
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
