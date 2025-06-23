<script lang="ts">
	import type { Message } from './base';
	import MessageBubble from './MessageBubble.svelte';

	interface Props {
		messages: Message[];
		subjectName: string;
		activeUntil?: number;
		onBubbleClick?: (index: number) => void;
	}
	let { messages, subjectName, activeUntil = -1, onBubbleClick = (index) => {} }: Props = $props();

	let chatDiv: HTMLElement;

	export function scrollToBottom(behavior?: 'auto' | 'instant' | 'smooth') {
		chatDiv.scrollTo({ top: chatDiv.scrollHeight, behavior });
	}
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
