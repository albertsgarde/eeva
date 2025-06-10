import { BACKEND_ORIGIN, expect, type InterviewId, type Message } from "$lib/base";
import { error } from '@sveltejs/kit';

export interface Interview {
    subjectName: string;
    messages: Message[];
}

export async function load({ params }: { params: { interviewId: string } }): Promise<{ interviewId: InterviewId, interview: Interview }> {
    const interviewId: number = parseInt(params.interviewId);
    if (interviewId < 0 || isNaN(interviewId)) {
        throw error(404, "Interview index must be a non-negative integer");
    }

    const url = `${BACKEND_ORIGIN}api/interview/${interviewId}`;
    const response = await fetch(url);
    if (!response.ok) {
        throw error(500, await response.text());
    }
    const interview: Interview = await response.json();

    return { interviewId: {id: interviewId}, interview }
}