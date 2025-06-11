import { env } from '$env/dynamic/public';

export const BACKEND_ORIGIN: URL = new URL(env.PUBLIC_BACKEND_ORIGIN || 'http://localhost:8000');

export function expect<T>(value: T | null, message: string): T {
    if (value === null || value === undefined) {
        throw new Error(message);
    }
    return value;
}

export interface CreateInterviewRequest {
    startMessageId: PromptId;
    interviewerSystemPromptId: PromptId;
    subjectName: string;
}

export interface InterviewId {
    id: number;
}

export interface PromptId {
    id: string;
}

const PROMPT_ID_REGEX = /^[a-zA-Z0-9\-]+$/;

export function createPromptId(id: string): PromptId {
    if (PROMPT_ID_REGEX.test(id))
        return { id };
    else {
        throw new Error(`Invalid prompt ID: ${id}. It must match the regex ${PROMPT_ID_REGEX}`);
    }
}

export interface Message {
    interviewer: boolean;
    content: string;
}