<script lang="ts">
	import '../app.css';
	let { children } = $props();
</script>

<div class="p-2 text-gray-100">
	{@render children()}
</div>
