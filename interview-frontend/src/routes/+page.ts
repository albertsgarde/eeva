import { expect } from "$lib/base";

interface CreateInterviewRequest {
    startMessageId: string;
    interviewerSystemPromptId: string;
}

export interface InterviewId {
    id: number;
}

export interface Message {
    interviewer: boolean;
    content: string;
}

export async function load({ url, fetch }): Promise<{ interviewId: InterviewId, messages: Message[] }> {
    const startMessageId = expect(url.searchParams.get('startMessageId'), 'startMessageId is required');
    const interviewerPromptId = expect(url.searchParams.get('interviewerPromptId'), 'interviewerPromptId is required');

    const createInterviewRequest: CreateInterviewRequest = {
        startMessageId: startMessageId,
        interviewerSystemPromptId: interviewerPromptId
    };

    const response: { interviewId: InterviewId, messages: Message[] } = await fetch(`/api/interview`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(createInterviewRequest)
    }).then(async (response) => {
        if (response.status !== 200) {
            const responseText = await response.text();
            throw new Error('Failed to create interview: ' + responseText);
        }
        return response.json();
    })
    return response;
}