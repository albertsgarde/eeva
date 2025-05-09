<script lang="ts">
	import IconSend from '@lucide/svelte/icons/send-horizontal';
	import { OpenAI } from 'openai';

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
			message: `start message`,
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
						content: `Can you try to interview me with the goal of placing me on this scale?: 📏 What the Scale Measures
The scale measures how much a person tries to shape how others perceive them through their language in an interview context.

Specifically, it gauges the degree to which someone is:

Actively packaging their statements in a way that signals, frames, or stylizes their identity, rather than just stating unprocessed facts or feelings.

⚖️ Scale Description (0.0 to 1.0)
Let’s break it into points on the continuum.

🔵 Low end (0.0 – 0.2): "Unpackaged Reality"
The speaker shares facts, events, or preferences plainly.

There’s no attempt to influence interpretation.

Responses are often reflective, but not curated.

No metaphor, drama, or moral framing is used.

The speaker seems indifferent to how they’re being perceived.

🧩 Key trait: They give you the pieces, not the story.

🟡 Middle range (0.3 – 0.7): "Partial Self-Stylization"
Some answers are plainly factual, others are clearly crafted to signal personality or values.

The speaker might occasionally use evocative phrasing, or explain why something matters.

There’s some effort to be understood, and some parts left raw.

The interviewee might reveal vulnerability—but how they do it varies.

They are inconsistently performative—real and stylized moments alternate.

🧩 Key trait: Some packaging, but it’s patchy—not a performance, not raw either.

🔴 High end (0.8 – 1.0): "Curated Identity Display"
The speaker actively shapes their narrative—they’re not just telling you what happened, they’re telling you what it means about who they are.

There’s strong use of emotionally loaded language, metaphor, self-awareness, or moral positioning.

Even flaws are framed strategically—e.g., "I’m intense, but only because I care deeply."

The person tries to guide your feelings about them—they might want to be seen as humble, resilient, misunderstood, bold, etc.

Their words signal personality, not just experiences.

🧩 Key trait: Their answers double as a mirror—reflecting their image back at you.

🧠 What the Scale Is Not Measuring
Not whether someone is smart or deep.

Not whether they’re being truthful.

Not whether they’re trying to impress you.

Not how dramatic their life has been.

It's only measuring:
👉 How much effort the speaker puts into shaping how you interpret who they are.

When you have a good idea of where I am just terminate the interview and tell me the score and expected standard deviation, it's okay that the standard deviation is just a vibe, the score will be too anyways. 
Right, interview time. I'm ready for my first question!`
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
