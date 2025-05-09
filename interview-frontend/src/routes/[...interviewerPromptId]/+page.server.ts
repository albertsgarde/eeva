import { readFile } from 'fs/promises';

export async function load({
	params
}: {
	params: { interviewerPromptId: string };
}): Promise<{ interviewerPrompt: string }> {
	const interviewer_prompt = await readFile(`../prompts/${params.interviewerPromptId}.txt`, 'utf-8');
	return { interviewerPrompt: interviewer_prompt };
}
