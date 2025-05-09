import type { Message } from "$lib/message";
import { mkdir, writeFile } from 'fs/promises';
import { dirname } from "path";

export async function POST({
	params,
	request
}: {
	params: { api_slug: string };
	request: Request;
}) {
	const { conversation_name, conversation }: {
		conversation_name: string, conversation: Message[]
	} = await request.json();

	const filePath = "../output/interviews/" + conversation_name + ".json";
	await mkdir(dirname(filePath), { recursive: true });
	await writeFile(filePath, JSON.stringify(conversation, null, 2), 'utf8')

	return new Response(JSON.stringify({ success: true }),)
}