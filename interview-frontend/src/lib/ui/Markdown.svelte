<script lang="ts">
	import MarkdownIt from 'markdown-it';
	export let content: string;

	const md = new MarkdownIt();
</script>

{@html md.render(content)}
