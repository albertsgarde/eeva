import { env } from '$env/dynamic/public';

export const BACKEND_ORIGIN: URL = new URL(env.PUBLIC_BACKEND_ORIGIN || 'http://localhost:8000');

export function expect<T>(value: T | null, message: string): T {
    if (value === null || value === undefined) {
        throw new Error(message);
    }
    return value;
}



export interface CreateInterviewRequest {
    startMessageId: string;
    interviewerSystemPromptId: string;
    subjectName: string;
}

export interface InterviewId {
    id: number;
}

export interface Message {
    interviewer: boolean;
    content: string;
}