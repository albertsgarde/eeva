<script lang="ts">
	interface Props {
		response: string;
		placeholder: string;
		onEnter?: () => void;
	}
	let { response = $bindable(''), placeholder, onEnter = () => {} }: Props = $props();

	function onKeyPress(event: KeyboardEvent) {
		if (['Enter'].includes(event.code)) {
			event.preventDefault();
			onEnter();
		}
	}
</script>

<input
	type="text"
	bind:value={response}
	class="m-0.5 w-full resize-none rounded border border-gray-600 bg-gray-700 p-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
	{placeholder}
	onkeypress={onKeyPress}
/>
