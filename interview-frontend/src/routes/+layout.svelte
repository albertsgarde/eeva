<script lang="ts">
	import '../app.css';
	let { children } = $props();
</script>

<div class="p-2">
	{@render children()}
</div>
