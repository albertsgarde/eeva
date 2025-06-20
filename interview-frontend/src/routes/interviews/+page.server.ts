import { expect, PromptId, type CreateInterviewRequest, type InterviewId, type Message } from "$lib/base";
import { redirect } from "@sveltejs/kit";

async function createInterview(
	startMessageId: PromptId,
	interviewerPromptId: PromptId,
	subjectName: string,
	fetch: (input: RequestInfo, init?: RequestInit) => Promise<Response>
): Promise<{ interviewId: InterviewId; messages: Message[] }> {
	const createInterviewRequest: CreateInterviewRequest = {
		startMessageId: startMessageId,
		interviewerSystemPromptId: interviewerPromptId,
		subjectName: subjectName
	};

	const response: { interviewId: InterviewId; messages: Message[] } = await fetch(
		`/api/interviews`,
		{
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(createInterviewRequest)
		}
	).then(async (response) => {
		if (response.status !== 200) {
			const responseText = await response.text();
			throw new Error('Failed to create interview: ' + responseText);
		}
		return response.json();
	});
	return response;
}


export async function load({ url, fetch }: { url: URL, fetch: any }): Promise<void> {
	const startMessageId = PromptId.parse(expect(url.searchParams.get('startMessageId'), 'startMessageId is required'));
	const interviewerPromptId = PromptId.parse(expect(url.searchParams.get('interviewerPromptId'), 'interviewerPromptId is required'));
	const subjectName: string = expect(url.searchParams.get('subjectName'), 'subjectName is required');

	const { interviewId, messages } = await createInterview(startMessageId, interviewerPromptId, subjectName, fetch);
	redirect(303, `/interview/${interviewId.id}`);
}