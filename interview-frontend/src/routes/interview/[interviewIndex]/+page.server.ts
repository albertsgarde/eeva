import { BACKEND_ORIGIN, expect, type Message } from "$lib/base";
import { error } from '@sveltejs/kit';

export interface Interview {
    subjectName: string;
    messages: Message[];
}

export async function load({ params }: { params: { interviewIndex: string } }): Promise<{ interview: Interview }> {
    const interviewIndex: number = parseInt(params.interviewIndex);
    if (interviewIndex < 0 || isNaN(interviewIndex)) {
        throw error(404, "Interview index must be a non-negative integer");
    }

    const url = `${BACKEND_ORIGIN}api/interview/${interviewIndex}`;
    const response = await fetch(url);
    if (!response.ok) {
        throw error(500, await response.text());
    }
    const interview: Interview = await response.json();

    return { interview: interview }
}