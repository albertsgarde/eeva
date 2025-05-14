import { readFile } from 'fs/promises';

export async function GET({
	url
}) {
	const promptId = url.searchParams.get('promptId');

	const filePath = "../prompts/" + promptId + ".txt";
	const prompt = await readFile(filePath, 'utf-8');

	return new Response(JSON.stringify(prompt),
		{
			headers: { "Content-Type": "application/json" },
			status: 200
		})
}