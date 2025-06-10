<script lang="ts">
	import '../app.css';
	let { children } = $props();
</script>

<div class="bg-gray-100">
	{@render children()}
</div>
