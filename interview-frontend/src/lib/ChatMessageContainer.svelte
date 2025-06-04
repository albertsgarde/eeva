<script lang="ts">
	import type { Message } from './base';
	import MessageBubble from './MessageBubble.svelte';

	export let messages: Message[];
	export let subjectName: string;

	let chatDiv: HTMLElement;

	export function scrollToBottom(behavior?: 'auto' | 'instant' | 'smooth') {
		chatDiv.scrollTo({ top: chatDiv.scrollHeight, behavior });
	}
</script>

<!-- Chat Messages Container -->
<div bind:this={chatDiv} class="flex-1 space-y-4 overflow-y-auto p-4">
	{#each messages as message}
		<MessageBubble {message} {subjectName} />
	{/each}
</div>
