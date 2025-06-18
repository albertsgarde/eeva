<script lang="ts">
	let { children } = $props();
</script>

<div class="min-h-screen bg-gray-800 p-6">
	{@render children()}
</div>
