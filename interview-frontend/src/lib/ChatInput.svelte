<script lang="ts">
	import IconSend from '@lucide/svelte/icons/send-horizontal';

	let currentMessage: string = '';

	function onPromptKeydown(event: KeyboardEvent) {
		if (['Enter'].includes(event.code)) {
			event.preventDefault();
			localSendMessage();
		}
	}

	function localSendMessage() {
		if (currentMessage.trim()) {
			sendMessage(currentMessage);
			currentMessage = '';
		}
	}

	export let sendMessage: (message: string) => Promise<void>;
</script>

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
			onclick={localSendMessage}
		>
			<IconSend />
		</button>
	</div>
</div>
