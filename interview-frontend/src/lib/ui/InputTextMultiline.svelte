<script lang="ts">
	interface Props {
		response: string;
		numRows: number;
		placeholder: string;
		onChange?: (event: Event) => void;
	}
	let { response = $bindable(''), numRows, placeholder, onChange }: Props = $props();
</script>

<textarea
	bind:value={response}
	onchange={onChange}
	class="m-0.5 w-full resize-none rounded border border-gray-600 bg-gray-700 p-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
	rows={numRows}
	{placeholder}
></textarea>
