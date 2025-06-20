<script lang="ts">
	export let onClick: () => Promise<void>;
	export let disabled: boolean = false;
</script>

<button
	class="mb-4 rounded bg-green-600 px-4 py-2 font-bold text-white hover:bg-green-700 focus:outline-none active:bg-green-800 disabled:cursor-not-allowed disabled:bg-gray-600 disabled:opacity-50"
	onclick={onClick}
	{disabled}
>
	<slot />
</button>
