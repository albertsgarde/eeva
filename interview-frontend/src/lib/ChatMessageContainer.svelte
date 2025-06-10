<script lang="ts">
	import type { Message } from './base';
	import MessageBubble from './MessageBubble.svelte';

	export let messages: Message[];
	export let subjectName: string;
	export let activeUntil: number = -1;

	let chatDiv: HTMLElement;

	export function scrollToBottom(behavior?: 'auto' | 'instant' | 'smooth') {
		chatDiv.scrollTo({ top: chatDiv.scrollHeight, behavior });
	}

	export let onBubbleClick: (index: number) => void = (index: number) => {};
</script>

<!-- Chat Messages Container -->
<div bind:this={chatDiv} class="flex-1 space-y-4 overflow-y-auto p-4">
	{#each messages as message, index}
		<MessageBubble
			{message}
			{subjectName}
			active={activeUntil == -1 || index <= activeUntil}
			onClick={() => onBubbleClick(index)}
		/>
	{/each}
</div>
