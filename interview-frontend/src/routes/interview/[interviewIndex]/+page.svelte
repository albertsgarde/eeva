<script lang="ts">
	import type { Message } from '$lib/base';
	import ChatFrame from '$lib/ChatFrame.svelte';
	import ChatMessageContainer from '$lib/ChatMessageContainer.svelte';
	import type { Interview } from './+page.server.ts';

	export let data: { interview: Interview };

	let { interview } = data;

	let elemChat: ChatMessageContainer;

	const curMessages: Message[] = interview.messages;
	const subjectName = interview.subjectName;
</script>

<!-- Body -->
<ChatFrame>
	<ChatMessageContainer bind:this={elemChat} messages={curMessages} {subjectName} />
</ChatFrame>
