import { expect } from "$lib/base";

export interface PageData {
    startMessageId: string;
    interviewerPromptId: string;
    subjectName: string | undefined;
}

export async function load({ url, fetch }): Promise<PageData> {
    const startMessageId = expect(url.searchParams.get('startMessageId'), 'startMessageId is required');
    const interviewerPromptId = expect(url.searchParams.get('interviewerPromptId'), 'interviewerPromptId is required');
    const subjectName = url.searchParams.get('subjectName');

    return {
        startMessageId,
        interviewerPromptId,
        subjectName: subjectName || undefined
    }
}