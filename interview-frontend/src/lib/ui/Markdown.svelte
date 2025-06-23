<script lang="ts">
	import MarkdownIt from 'markdown-it';
	interface Props {
		content: string;
	}
	let { content }: Props = $props();

	const md = new MarkdownIt();
</script>

{@html md.render(content)}
